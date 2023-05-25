import glob
import json
import os
import pytest

import clr  # noqa: F401
import typer
# from xml.dom import minidom
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient
from azure.core.rest import HttpRequest
from Kusto.Language import GlobalState  # noqa: E402,F401
from Kusto.Language import KustoCode  # noqa: E402,F401
from Kusto.Language.Symbols import DatabaseSymbol  # noqa: E402,F401,E501
from Kusto.Language.Symbols import TableSymbol  # noqa: E402,F401,E501
from Kusto.Language.Symbols import FunctionSymbol  # noqa: E402,F401,E501
from yaml import safe_load
from jinja2 import Template
from .models.detection import Detection

app = typer.Typer()


class Workspace:
    def __init__(self, tables: list, functions: list) -> None:
        self.tables = tables
        self.functions = functions

    @property
    def global_state(self) -> GlobalState:
        ''' Generate global state. Used for table/field validation '''
        state = GlobalState.Default.WithDatabase(DatabaseSymbol('db', *self.symbols))
        return state

    @property
    def symbols(self) -> list[TableSymbol]:
        ''' Generate list of Symbols. Used for table/field validation '''
        all_symbols = []
        if self.tables:
            for table, columns in self.tables.items():
                field_list = ','.join([f'{column["name"]}: {column["type"]}' for column in columns])
                table_symbol = TableSymbol(table, f'({field_list})')
                all_symbols.append(table_symbol)

        if self.functions:
            for function, values in self.functions.items():
                function_symbol = FunctionSymbol(function, f'({values["params"]})', f'{{ {values["body"]} }}')
                all_symbols.append(function_symbol)

        return all_symbols

    def to_json(self, output_path: 'str') -> None:
        ''' Dump schema to JSON '''
        # Write tables and functions to file
        with open(f'{output_path}', 'w') as outputfile:
            outputfile.write(json.dumps({'functions': self.functions,
                                         'tables': self.tables}, indent=2))

    @classmethod
    def from_file(cls, path: str) -> 'Workspace':
        ''' Initialise class from schema file '''
        with open(path, 'r') as schemafile:
            global_schema = json.loads(schemafile.read())
            return cls(tables=global_schema['tables'], 
                       functions=global_schema['functions'])

    @classmethod
    def from_api(cls, credential: 'DefaultAzureCredential', workspace_id: str) -> 'Workspace':
        ''' Initialse class via API '''

        logs_client = LogsQueryClient(credential)

        # Request workspace metadata containing tables and both custom + default functions
        header = {'prefer': 'metadata-format-v4,exclude-customlogs,exclude-customfields,wait=180'}
        request = HttpRequest(url=f'workspaces/{workspace_id}/metadata?select=tables,functions',
                              method='GET', headers=header)
        response = logs_client._client.send_request(request).json()

        # # Populate dictionary containing key/value pairs of tables with it's fields/types
        tables = {table['name']: [{'name': column['name'], 'type': column['type']} for column in table['columns']]
                  for table in response['tables']}
        functions = {function['name']: {'body': function['body'], 'params': function.get('parameters')}
                     for function in response['functions']}
        return cls(tables=tables, functions=functions)


class KQL(Detection):
    def validate(self, workspace):
        global_state = workspace.global_state
        kql = KustoCode.ParseAndAnalyze(self.query, global_state)
        diagnostics = kql.GetDiagnostics()
        errors = [{
            'severity': diag.Severity,
            'message': diag.Message,
            'start': diag.Start,
            'end': diag.End,
            'issue': self.query[diag.Start:diag.End]
            } for diag in diagnostics if diagnostics.Count > 0]  # noqa: E123
        return errors


class SentinelDetections:
    def __init__(self, detections: list[Detection], workspace: Workspace, **kwargs) -> None:
        self.workspace = workspace
        self.detections = detections
        self.kwargs = kwargs

    def validate(self) -> dict[str, str]:
        ''' Validates if KQL queries are parsed correctly '''
        global_state = self.workspace.global_state
        for detection in self.detections:
            error_messages = []
            kql = KustoCode.ParseAndAnalyze(detection.query, global_state)
            diagnostics = kql.GetDiagnostics()
            if (diagnostics.Count > 0):
                for diag in diagnostics:
                    error_messages.append({
                        'severity': diag.Severity,
                        'message': diag.Message,
                        'issue': detection.query[diag.Start:diag.End]
                    })
            yield detection.name, detection.query, error_messages

    @classmethod
    def from_yaml(cls, path: str, **kwargs) -> 'SentinelDetections':
        ''' Initialised class based on path where detection content is saved '''
        parsed_content = []
        detection_files = glob.glob(f'{path}/**/*.yaml', recursive=True)
        for detection in detection_files:
            with open(detection, 'r') as detectionfile:
                data = safe_load(detectionfile)
                parsed_content.append(KQL(**data))
        return cls(detections=parsed_content, **kwargs)

    def to_markdown(self, path: str, template: str = 'templates/detection.md') -> None:
        current_path = os.path.dirname(__file__)
        full_path = os.path.join(current_path, template)
        with open(full_path, 'r') as template_file:
            template = Template(template_file.read())

        for detection in self.detections:
            rendered_file = template.render(detection)
            out_file_name = f'{path}/{detection.id}.md'
            with open(out_file_name, 'w') as outfile:
                outfile.write(rendered_file)


class PytestValidation:
    def pytest_addoption(self, parser):
        default_path = os.path.dirname(__file__)
        parser.addoption('--detections', action='store',
                default=default_path, help='Path containing detection content')
        parser.addoption('--schema', default=None, action='store',
                help='Path containing schema')

    def pytest_generate_tests(self, metafunc):
        if 'detections' in metafunc.fixturenames:
            path = metafunc.config.getoption('detections')
            if metafunc.config.getoption('schema'):
                workspace = Workspace.from_file(metafunc.config.getoption('schema'))
            else:
                workspace = Workspace(tables=None, functions=None)

            detections = SentinelDetections.from_yaml(path, workspace=workspace)
            results = [{'name': name, 'query': query, 'results': results}
                    for name, query, results in detections.validate()]
            metafunc.parametrize("detections", results, ids=[result['name']
                                                            for result in results])



@app.command()
def validate(path: str, schema: str) -> None:
    ''' Validate KQL files using KustoLanguageDll + synced schema '''

    # Initialise workspace with schema
    workspace = Workspace.from_file(schema)

    # Load detection content from path
    detections = SentinelDetections.from_yaml(path, workspace=workspace)
    for detection in detections.detections:
        print(detection.validate(workspace))


@app.command()
def letest(detections):
    pytest.main(["test_stages", f'--detections={detections}'],
                plugins=[PytestValidation()])
    # print(detections.to_junitxml('/tmp/test.json'))


@app.command()
def sync(path: str, workspace: str) -> None:
    ''' Sync Log Analytics workspace tables/fields '''
    # Use default authentication client
    credential = DefaultAzureCredential()
    workspace = Workspace.from_api(credential, workspace_id=workspace)
    workspace.to_json(path)

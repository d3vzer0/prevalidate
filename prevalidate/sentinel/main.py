import glob
import json

import clr  # noqa: F401
import typer
from azure.identity import DefaultAzureCredential
from azure.mgmt.loganalytics import LogAnalyticsManagementClient
from azure.monitor.query import LogsQueryClient
from azure.core.rest import HttpRequest
from Kusto.Language import GlobalState  # noqa: E402,F401
from Kusto.Language import KustoCode  # noqa: E402,F401
from Kusto.Language.Symbols import DatabaseSymbol  # noqa: E402,F401,E501
from Kusto.Language.Symbols import TableSymbol  # noqa: E402,F401,E501
from Kusto.Language.Symbols import FunctionSymbol # noqa: E402,F401,E501
from yaml import safe_load
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
        for table, columns in self.tables.items():
            field_list = ','.join([f'{column["name"]}: {column["type"]}' for column in columns])
            table_symbol = TableSymbol(table, f'({field_list})')
            all_symbols.append(table_symbol)

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


class SentinelDetections:
    def __init__(self, detections: list[Detection], workspace: Workspace, **kwargs) -> None:
        self.workspace = workspace
        self.detections = detections
        self.kwargs = kwargs

    def validate(self) -> dict[str, str]:
        ''' Validates if KQL queries are parsed correctly '''
        global_state = self.workspace.global_state
        for detection in self.detections:
            kql = KustoCode.ParseAndAnalyze(detection.query, global_state)
            diagnostics = kql.GetDiagnostics()
            if (diagnostics.Count > 0):
                for diag in diagnostics:
                    message = {
                        'name': detection.name,
                        'query': detection.query,
                        'severity': diag.Severity,
                        'message': diag.Message,
                        'issue': detection.query[diag.Start:diag.End]
                    }
                    yield message

    @classmethod
    def from_yaml(cls, path: str, **kwargs) -> 'SentinelDetections':
        ''' Initialised class based on path where detection content is saved '''
        detection_files = glob.glob(f'{path}/*.yaml', recursive=True)
        parsed_content = []
        for detection in detection_files:
            with open(detection, 'r') as detectionfile:
                data = safe_load(detectionfile)
                parsed_content.append(Detection(**data))
        return cls(detections=parsed_content, **kwargs)


@app.command()
def validate(path: str, schema: str) -> None:
    ''' Validate KQL files using KustoLanguageDll + synced schema '''

    # Initialise workspace with schema
    workspace = Workspace.from_file(schema)

    # Load detection content from path
    detections = SentinelDetections.from_yaml(path, workspace=workspace)

    # Check if KQL queries are parsed correctly
    for issue in detections.validate():
        print(issue)


@app.command()
def sync(path: str, workspace: str) -> None:
    ''' Sync Log Analytics workspace tables/fields '''
    # Use default authentication client
    credential = DefaultAzureCredential()
    workspace = Workspace.from_api(credential, workspace_id=workspace)
    workspace.to_json(path)

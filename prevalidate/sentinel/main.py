import glob
import json

import clr  # noqa: F401
import typer
from azure.identity import DefaultAzureCredential
from azure.mgmt.loganalytics import LogAnalyticsManagementClient
from Kusto.Language import GlobalState  # noqa: E402,F401
from Kusto.Language import KustoCode  # noqa: E402,F401
from Kusto.Language.Symbols import DatabaseSymbol  # noqa: E402,F401,E501
from Kusto.Language.Symbols import TableSymbol  # noqa: E402,F401,E501
from yaml import safe_load
from .models.detection import Detection

app = typer.Typer()


class Workspace:
    def __init__(self, schema: str) -> None:
        self.schema = schema

    @property
    def global_state(self) -> GlobalState:
        ''' Generate global state. Used for table/field validation '''
        state = GlobalState.Default.WithDatabase(DatabaseSymbol('db', *self.symbols))
        return state

    @property
    def symbols(self) -> list[TableSymbol]:
        ''' Generate list of Symbols. Used for table/field validation '''
        table_symbols = []
        for table, fields in self.schema.items():
            field_list = ','.join([f'{fname}: {ftype}' for fname, ftype in fields.items()])
            symbol_object = TableSymbol(table, f'({field_list})')
            table_symbols.append(symbol_object)
        return table_symbols

    def to_json(self, output_path: 'str') -> None:
        ''' Dump schema to JSON '''
        # Write tables to file
        with open(f'{output_path}/schema.json', 'w') as outputfile:
            outputfile.write(json.dumps(self.schema, indent=2))

    @classmethod
    def from_file(cls, path: str) -> 'Workspace':
        ''' Initialise class from schema file '''
        with open(path, 'r') as schemafile:
            global_schema = json.loads(schemafile.read())
            return cls(schema=global_schema)

    @classmethod
    def from_api(cls, credential: 'DefaultAzureCredential', subscription: str, 
                 rgroup: str, workspace: str) -> 'Workspace':
        ''' Initialse class via API '''
        # Initialise LogAnalyticsManagementClient
        client = LogAnalyticsManagementClient(credential, subscription)

        # List all tables/fields from specified workspace name
        tables = client.tables.list_by_workspace(resource_group_name=rgroup, workspace_name=workspace)

        # Populate dictionary containing key/value pairs of tables with it's fields/types
        schema_results = {}
        for table in tables:
            standard_columns = {col.name: col.type for col in table.schema.standard_columns}
            custom_columns = {col.name: col.type for col in table.schema.columns} \
                if table.schema.columns else {}
            schema_results[table.schema.name] = {**standard_columns, **custom_columns}
    
        return cls(schema=schema_results)


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
def validate(path: str, schema: str):
    ''' Validate KQL files using KustoLanguageDll + synced schema '''

    # Initialise workspace with schema
    workspace = Workspace.from_file(schema)

    # Load detection content from path
    detections = SentinelDetections.from_yaml(path, workspace=workspace)

    # Check if KQL queries are parsed correctly
    for issue in detections.validate():
        print(issue)


@app.command()
def functions(path: str, subscription: str, rgroup: str, workspace: str):
    ''' Sync Log Analytics workspace tables/fields '''

    # Use default authentication client
    credential = DefaultAzureCredential()
    workspace = Workspace.from_api(credential, subscription, rgroup, workspace)

    # Initialise LogAnalyticsManagementClient
    client = LogAnalyticsManagementClient(credential, subscription)
    saved_searches = client.saved_searches.list_by_workspace(resource_group_name=rgroup, workspace_name=workspace)

    custom_functions = []
    for search in saved_searches.value:
        print(search)
    #     if search.function_alias:
    #         custom_functions.append(search.function_alias)

    # with open(f'{path}/functions.json', 'w') as outputfile:
    #     outputfile.write(json.dumps(custom_functions, indent=2))


@app.command()
def tables(path: str, subscription: str, rgroup: str, workspace: str):
    ''' Sync Log Analytics workspace tables/fields '''
    # Use default authentication client
    credential = DefaultAzureCredential()
    workspace = Workspace.from_api(credential, subscription, rgroup, workspace)
    workspace.to_json(path)

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


app = typer.Typer()


@app.command()
def validate(path: str, schema: str):
    ''' Validate KQL files using KustoLanguageDll + synced schema '''
    # Open and parse schema file
    with open(schema, 'r') as schemafile:
        global_schema = json.loads(schemafile.read())

    # Create list Symbols for GlobalState
    table_symbols = []
    for table, fields in global_schema.items():
        field_list = ','.join([f'{fname}: {ftype}' for fname, ftype in fields.items()])
        symbol_object = TableSymbol(table, f'({field_list})')
        table_symbols.append(symbol_object)

    # Initialise Global state to analyse KQL queries
    global_state = GlobalState.Default.WithDatabase(DatabaseSymbol('db', *table_symbols))

    # Iterate over KQL files, replace later
    kql_files = glob.glob(f'{path}/*.kql', recursive=True)
    for kql in kql_files:
        with open(kql, 'r') as kql_file:
            kql_content = kql_file.read()
            print(kql_content)
            code = KustoCode.ParseAndAnalyze(kql_content, global_state)
            diagnostics = code.GetDiagnostics()
            if (diagnostics.Count > 0):
                for diag in diagnostics:
                    message = {
                        'query': kql_content,
                        'severity': diag.Severity,
                        'message': diag.Message,
                        'length': diag.Length,
                        'start': diag.Start,
                        'end': diag.End,
                        'troublemaker': kql_content[diag.Start:diag.End]
                    }
                    print(message)


@app.command()
def sync(path: str, subscription: str, rgroup: str, workspace: str):
    ''' Sync Log Analytics workspace tables/fields '''

    # Use default authentication client
    credential = DefaultAzureCredential()

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

    # Write tables to file
    with open(f'{path}.json', 'w') as outputfile:
        outputfile.write(json.dumps(schema_results, indent=2))

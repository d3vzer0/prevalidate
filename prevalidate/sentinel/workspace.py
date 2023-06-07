import clr  # noqa: F401
from Kusto.Language import GlobalState  # noqa: E402,F401
from Kusto.Language.Symbols import DatabaseSymbol  # noqa: E402,F401,E501
from Kusto.Language.Symbols import TableSymbol  # noqa: E402,F401,E501
from Kusto.Language.Symbols import FunctionSymbol  # noqa: E402,F401,E501
from azure.monitor.query import LogsQueryClient
from azure.core.rest import HttpRequest
import json
import glob

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

    def to_json(self, output_path: 'str', single: bool = True) -> None:
        ''' Dump schema to JSON '''
        if single:
            # Write tables and functions to single file
            with open(f'{output_path}', 'w') as outputfile:
                outputfile.write(json.dumps({'functions': self.functions,
                                            'tables': self.tables}, indent=2))
        else:
            # Write tables and functions to split files
            # Write seperate functions
            for function, content in self.functions.items():
                with open(f'{output_path}/functions/{function}.json', 'w') as functionfile:
                    functionfile.write(json.dumps({function: content}))
    
            # Write seperate tables
            for table, content in self.tables.items():
                with open(f'{output_path}/tables/{table}.json', 'w') as tablefile:
                    tablefile.write(json.dumps({table: content}))

    @classmethod
    def from_files(cls, path: str) -> 'Workspace':
        ''' Initialse class by loading schema files '''
        tables = {}
        # For all json files in tables directory, load object
        table_files = glob.glob(f'{path}/tables/*.json')
        for table in table_files:
            with open(table, 'r') as table_file:
                table_object = json.loads(table_file.read())
                tables = {**tables, **table_object}

        functions = {}
        # For all json files in functions directory, load object
        function_files = glob.glob(f'{path}/functions/*json')
        for function in function_files:
            with open(function, 'r') as function_file:
                function_object = json.loads(function_file.read())
                functions = {**functions, **function_object}
        
        return cls(tables=tables, functions=functions)

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

        # Populate dictionary containing key/value pair of functions and its contents
        functions = {function['name']: {'body': function['body'], 'params': function.get('parameters')}
                     for function in response['functions']}
        return cls(tables=tables, functions=functions)

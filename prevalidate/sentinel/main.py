import os
import pytest
import typer
from azure.identity import DefaultAzureCredential
from .plugins import PytestValidation
from .workspace import Workspace

app = typer.Typer()


valid_options = ['yaml','kql']

@app.command()
def test(detections: str, schema: str, format: str = typer.Option(default="yaml", help="Format of files")) -> None:
    current_dir = os.path.dirname(__file__)
    test_dir = os.path.join(current_dir, 'test_stages')
    pytest.main([test_dir, f'--detections={detections}', 
                 f'--schema={schema}', "--junitxml=./results.xml",
                 f"--format={format}",
                 "-s", "--tb=line"],
                plugins=[PytestValidation()])


@app.command()
def sync(path: str, workspace: str) -> None:
    ''' Sync Log Analytics workspace tables/fields '''
    # Use default authentication client
    credential = DefaultAzureCredential()
    workspace = Workspace.from_api(credential, workspace_id=workspace)
    workspace.to_json(path, single=False)

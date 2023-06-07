import os
import pytest
import typer
from azure.identity import DefaultAzureCredential
from .plugins import PytestValidation
from .workspace import Workspace

app = typer.Typer()


# @app.command()
# def validate(path: str, schema: str) -> None:
#     ''' Validate KQL files using KustoLanguageDll + synced schema '''

#     # Initialise workspace with schema
#     workspace = Workspace.from_file(schema)

#     # Load detection content from path
#     detections = SentinelDetections.from_yaml(path, workspace=workspace)
#     for detection in detections.detections:
#         print(detection.validate(workspace))


@app.command()
def unittest(detections, schema):
    current_dir = os.path.dirname(__file__)
    test_dir = os.path.join(current_dir, 'test_stages')
    pytest.main([test_dir, f'--detections={detections}', f'--schema={schema}', "--junitxml=./example.xml", "-s"],
                plugins=[PytestValidation()])


@app.command()
def sync(path: str, workspace: str) -> None:
    ''' Sync Log Analytics workspace tables/fields '''
    # Use default authentication client
    credential = DefaultAzureCredential()
    workspace = Workspace.from_api(credential, workspace_id=workspace)
    workspace.to_json(path, single=False)

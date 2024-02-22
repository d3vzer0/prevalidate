from azure.identity import DefaultAzureCredential
from prevalidate.sentinel.detections import SentinelDetections, KQL
from prevalidate.sentinel.main import Workspace
import os

BASE_PATH = os.path.dirname(__file__)


def test_validate():
    schema_file = os.path.join(BASE_PATH, 'test_data/sentinel/schema.json')
    detections_dir = os.path.join(BASE_PATH, 'test_data/sentinel/detections')

    workspace = Workspace.from_file(schema_file)
    detections = SentinelDetections.from_yaml(detections_dir, workspace=workspace)
    issues = [issues for name, query, issues in detections.validate() if issues]
    assert len(issues) == 2


def test_validate_plain():
    schema_file = os.path.join(BASE_PATH, 'test_data/sentinel/schema.json')
    detections_dir = os.path.join(BASE_PATH, 'test_data/kql')

    workspace = Workspace.from_file(schema_file)
    detections = SentinelDetections.from_plain(detections_dir, workspace=workspace)
    issues = [issues for name, query, issues in detections.validate() if issues]
    assert len(issues) == 2


def test_workspace_file():
    schema_file = os.path.join(BASE_PATH, 'test_data/sentinel/schema.json')
    workspace = Workspace.from_file(schema_file)
    assert workspace.functions and workspace.tables


# def test_workspace_api():
#     credential = DefaultAzureCredential()
#     workspace = Workspace.from_api(credential, '')
#     workspace.to_json('schema.json')
#     assert workspace.functions and workspace.tables

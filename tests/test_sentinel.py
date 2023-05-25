from azure.identity import DefaultAzureCredential
from prevalidate.sentinel.main import Workspace, SentinelDetections
from azure.monitor.query import LogsQueryClient
from datetime import datetime, timedelta
from azure.core.rest import HttpRequest
from prevalidate.sentinel.main import Workspace
import requests
import os

BASE_PATH = os.path.dirname(__file__)


def test_detections_to_markdown():
    detections_dir = os.path.join(BASE_PATH, 'test_data/sentinel/detections')
    detections = SentinelDetections.from_yaml(detections_dir, workspace=None)
    detections.to_markdown('../test')


def test_validate():
    schema_file = os.path.join(BASE_PATH, 'test_data/sentinel/schema.json')
    detections_dir = os.path.join(BASE_PATH, 'test_data/sentinel/detections')

    workspace = Workspace.from_file(schema_file)
    detections = SentinelDetections.from_yaml(detections_dir, workspace=workspace)
    issues = [issue for issue in detections.validate()]
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

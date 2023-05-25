from azure.identity import DefaultAzureCredential
from prevalidate.sentinel.main import Workspace, SentinelDetections
from azure.monitor.query import LogsQueryClient
from datetime import datetime, timedelta
from azure.core.rest import HttpRequest
from prevalidate.sentinel.main import Workspace
import requests
import os


def test_detections_to_markdown():
    detections = SentinelDetections.from_yaml('tests/test_data/sentinel/detections', workspace=None)
    detections.to_markdown('../test')


def test_validate():
    workspace = Workspace.from_file('./schema.json')
    detections = SentinelDetections.from_yaml('tests/test_data/sentinel/detections', workspace=workspace)
    issues = [issue for issue in detections.validate()]
    assert len(issues) == 1


def test_workspace_file():
    workspace = Workspace.from_file('./schema.json')
    assert workspace.functions and workspace.tables


# def test_workspace_api():
#     credential = DefaultAzureCredential()
#     workspace = Workspace.from_api(credential, '')
#     workspace.to_json('schema.json')
#     assert workspace.functions and workspace.tables

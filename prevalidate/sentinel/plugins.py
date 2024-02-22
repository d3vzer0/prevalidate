
from .workspace import Workspace
import os
import glob


class PytestValidation:
    def pytest_addoption(self, parser):
        default_path = os.path.dirname(__file__)
        parser.addoption('--detections', action='store',
                default=default_path, help='Path containing detection content')
        parser.addoption('--schema', default=None, action='store',
                help='Path containing schema')
        parser.addoption('--format', default='yaml', action='store',
                help='Path containing schema')

    def pytest_generate_tests(self, metafunc):
        if 'detections' in metafunc.fixturenames:
            path = metafunc.config.getoption('detections')
            schema = metafunc.config.getoption('schema')
            format = metafunc.config.getoption('format')

            if schema:
                workspace = Workspace.from_files(schema)
            else:
                workspace = Workspace(tables=None, functions=None)

            format = 'yaml' if format == 'yaml' else 'kql'
            detection_files = glob.glob(f'{path}/**/*.{format}', recursive=True)
            detections = [{'path': detection, 'schema': workspace, 'format': format} for detection in detection_files]
            metafunc.parametrize("detections", detections, ids=[det for det in detection_files])

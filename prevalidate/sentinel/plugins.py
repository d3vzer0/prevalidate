
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

    def pytest_generate_tests(self, metafunc):
        if 'detections' in metafunc.fixturenames:
            path = metafunc.config.getoption('detections')
            schema = metafunc.config.getoption('schema')
            if schema:
                workspace = Workspace.from_files(schema)
            else:
                workspace = Workspace(tables=None, functions=None)

            detection_files = glob.glob(f'{path}/**/*.yaml', recursive=True)
            detections = [{'path': detection, 'schema': workspace} for detection in detection_files]
            metafunc.parametrize("detections", detections, ids=[det for det in detection_files])

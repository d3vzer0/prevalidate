import clr  # noqa: F401
from .models.detection import Detection, PlainDetection
from pydantic.error_wrappers import ValidationError
from Kusto.Language import KustoCode  # noqa: E402,F401
from .workspace import Workspace
from yaml import safe_load
from .workspace import Workspace
from jinja2 import Template
import os
import glob


class SentinelKQL(Detection):
    def validate(self, workspace: 'Workspace') -> list[dict]:
        global_state = workspace.global_state
        kql = KustoCode.ParseAndAnalyze(self.query, global_state)
        diagnostics = kql.GetDiagnostics()
        errors = [{
            'severity': diag.Severity,
            'message': diag.Message,
            'start': diag.Start,
            'end': diag.End,
            'issue': self.query[diag.Start:diag.End]
            } for diag in diagnostics if diagnostics.Count > 0]  # noqa: E123
        return errors


class KQL(PlainDetection):
    def validate(self, workspace: 'Workspace') -> list[dict]:
        global_state = workspace.global_state
        kql = KustoCode.ParseAndAnalyze(self.query, global_state)
        diagnostics = kql.GetDiagnostics()
        errors = [{
            'severity': diag.Severity,
            'message': diag.Message,
            'start': diag.Start,
            'end': diag.End,
            'issue': self.query[diag.Start:diag.End]
            } for diag in diagnostics if diagnostics.Count > 0]  # noqa: E123
        return errors


class SentinelDetections:
    def __init__(self, detections: list[Detection], workspace: Workspace, **kwargs) -> None:
        self.workspace = workspace
        self.detections = detections
        self.kwargs = kwargs

    def validate(self) -> dict[str, str]:
        """Validates if KQL queries are parsed correctly

        Returns:
            dict[str, str]: _description_

        Yields:
            Iterator[dict[str, str]]: _description_
        """
        global_state = self.workspace.global_state
        for detection in self.detections:
            error_messages = []
            kql = KustoCode.ParseAndAnalyze(detection.query, global_state)
            diagnostics = kql.GetDiagnostics()
            if (diagnostics.Count > 0):
                for diag in diagnostics:
                    error_messages.append({
                        'severity': diag.Severity,
                        'message': diag.Message,
                        'issue': detection.query[diag.Start:diag.End]
                    })
            yield detection.name, detection.query, error_messages

    @classmethod
    def from_yaml(cls, path: str, **kwargs) -> 'SentinelDetections':
        """Initialised class based on path where detection content is saved

        Args:
            path (str): Path to files containing Sentinel content (yaml)

        Returns:
            SentinelDetections: _description_
        """
        parsed_content = []
        detection_files = glob.glob(f'{path}/**/*.yaml', recursive=True)
        for detection in detection_files:
            with open(detection, 'r') as detectionfile:
                data = safe_load(detectionfile)
                try:
                    parsed_content.append(SentinelKQL(**data))
                except ValidationError as err:
                    pass
        return cls(detections=parsed_content, **kwargs)
    
    @classmethod
    def from_plain(cls, path: str, **kwargs) -> 'SentinelDetections':
        """Initialised class based on path with plain KQL where detection content is saved

        Args:
            path (str): Path to files containing Kusto queries (plain)

        Returns:
            SentinelDetections: _description_
        """
        parsed_content = []
        detection_files = glob.glob(f'{path}/**/*.kql', recursive=True)
        for detection in detection_files:
            with open(detection, 'r') as detectionfile:
                try:
                    data = {'name': detection, 'query': detectionfile.read()}
                    parsed_content.append(KQL(**data))
                except ValidationError as err:
                    pass
        return cls(detections=parsed_content, **kwargs)

    def to_markdown(self, path: str, template: str = 'templates/detection.md') -> None:
        """Export content as markdown docs

        Args:
            path (str): _description_
            template (str, optional): _description_. Defaults to 'templates/detection.md'.
        """
        current_path = os.path.dirname(__file__)
        full_path = os.path.join(current_path, template)
        with open(full_path, 'r') as template_file:
            template = Template(template_file.read())

        for detection in self.detections:
            rendered_file = template.render(detection)
            out_file_name = f'{path}/{detection.id}.md'
            with open(out_file_name, 'w') as outfile:
                outfile.write(rendered_file)

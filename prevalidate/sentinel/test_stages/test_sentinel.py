from prevalidate.sentinel.detections import KQL
from prevalidate.sentinel.workspace import Workspace
from yaml import safe_load
from pydantic import ValidationError


def test_format(detections):
    with open(detections['path'], 'r') as detectionfile:
        data = safe_load(detectionfile)
        try:
            kql_content = KQL(**data)
        except ValidationError as err:
            error_content = [{'field': error._loc, 'error': error.exc.msg_template} for error in err.raw_errors]
            kql_content = error_content

    assert isinstance(kql_content, KQL), f'{kql_content}'


def test_query(detections):
    with open(detections['path'], 'r') as detectionfile:
        data = safe_load(detectionfile)
        try:
            kql_content = KQL(**data)
        except ValidationError as err:
            pass

        parse_failures = kql_content.validate(detections['schema'])
        assert len(parse_failures) == 0, parse_failures
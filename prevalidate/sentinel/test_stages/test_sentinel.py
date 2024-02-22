from prevalidate.sentinel.detections import KQL, SentinelKQL
from prevalidate.sentinel.workspace import Workspace
from yaml import safe_load
from pydantic import ValidationError


def load_content(path: str, format: str):
    """Load the file depending on the format

    Args:
        detections (_type_): _description_
    """
    with open(path, 'r') as detectionfile:
        if format == 'yaml':
            data = safe_load(detectionfile)
            kql_content = SentinelKQL, SentinelKQL(**data)
        else:
            data = {'name': path, 'query': detectionfile.read()}
            kql_content = KQL, KQL(**data)

    return kql_content

def test_format(detections):
    """Test the returned object is of the correct type (ie. KQL or SentinelKQL)

    Args:
        detections (_type_): _description_
    """
    try:
        kql_type, kql_content = load_content(detections['path'], detections['format'])
    except ValidationError as err:
        error_content = [{'field': error._loc, 'error': error.exc.msg_template} for error in err.raw_errors]
        kql_content = error_content

    assert isinstance(kql_content, kql_type), f'{kql_content}'


def test_query(detections):
    """Test the query succesfully validates usingt he KQL tester

    Args:
        detections (_type_): _description_
    """
    try:
        kql_type, kql_content = load_content(detections['path'], detections['format'])
    except ValidationError as err:
        pass

    parse_failures = kql_content.validate(detections['schema'])
    assert len(parse_failures) == 0, parse_failures
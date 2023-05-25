def test_detections(detections):
    messages = [result['message'] for result in detections['results']]
    assert len(detections['results']) == 0, f'{"".join(messages)}'

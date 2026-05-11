from app.skills.scheduling import handle_scheduling


def test_destructive_request_is_blocked():
    message = handle_scheduling({'request': 'Delete tomorrow meeting'})
    assert 'requires explicit HITL approval' in message

import pytest

import util.cleanup as cleanup
from util.http_request import HTTPRequest

@pytest.fixture(scope="function")
def session(session, request):
    # finalisers are popped off a stack,
    # making their ordering reverse
    request.addfinalizer(lambda: cleanup.switch_to_top_level_browsing_context(session))
    request.addfinalizer(lambda: cleanup.restore_windows(session))
    request.addfinalizer(lambda: cleanup.dismiss_user_prompts(session))

    return session

@pytest.fixture(scope="module")
def http(session):
    return HTTPRequest(session.transport.host, session.transport.port)

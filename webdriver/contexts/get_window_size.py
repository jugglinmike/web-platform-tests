from util import wd_assert
from util.assert_window_rect import assert_rect_spec, assert_post_response

def test_window_size_types(session):
    session.start()
    result = session.send_raw_command("GET", "window/rect")

    assert_rect_spec(result)

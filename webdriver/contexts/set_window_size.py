from util.assert_window_rect import assert_rect_spec, assert_post_response

# These tests must not specify expectations for window position/location
# following "resize" or "reposition" operations as the specification
# allows this behavior to be implementation-defined.
#
# WebDriver specification ID: set-window-rect
#
# > NOTE
# >
# > The specification does not guarantee that the resulting window size will
# > exactly match that which was requested. In particular the implementation is
# > expected to clamp values that are larger than the physical screen
# > dimensions, or smaller than the minimum window size.
# >
# > Particular implementations may have other limitations such as not being
# > able to resize in single-pixel increments.

def test_set_window_size(session):
    result = session.send_raw_command("POST", "window/rect", dict(width=400, height=500))

    assert_post_response(result)

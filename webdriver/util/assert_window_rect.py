import os

# WebDriver specification ID: dfn-window-rect
#
# > A top-level browsing context’s window rect is defined as a dictionary of
# > the screenX, screenY, width and height attributes of the WindowProxy. Its
# > JSON representation is the following:
# >
# > x
# >     WindowProxy’s screenX attribute.
# > y
# >     WindowProxy’s screenY attribute.
# > width
# >     Width of the top-level browsing context’s outer dimensions, including
# >     any browser chrome and externally drawn window decorations in CSS
# >     reference pixels.
# > height
# >     Height of the top-level browsing context’s outer dimensions, including
# >     any browser chrome and externally drawn window decorations in CSS
# >     reference pixels.
def assert_rect_spec(result):
    assert result.status == 200
    assert "value" in result.body

    assert "width" in result.body["value"]
    assert "height" in result.body["value"]
    assert isinstance(result.body["value"]["width"], int)
    assert isinstance(result.body["value"]["height"], int)

    assert "x" in result.body["value"]
    assert "y" in result.body["value"]
    assert isinstance(result.body["value"]["x"], int)
    assert isinstance(result.body["value"]["y"], int)

# WebDriver specification ID: set-window-rect
#
# > [...]
# > 3. If the remote end does not support the Set Window Rect command for the
# >    current top-level browsing context for any reason, return error with
# >    error code unsupported operation.
def assert_not_supported(result):
    wd_assert.error(result, "unsupported operation")

# WebDriver specification ID: resizing-and-positioning-windows
#
# > Because different operating system’s window managers provide different
# > abilities, not all of the commands in this section can be supported by all
# > remote ends. Where a command is not supported, an unsupported operation
# > error is returned.
if "WD_NON_INTERACTIVE_WINDOW" in os.environ:
    assert_post_response = assert_not_impemented
else:
    assert_post_response = assert_rect_spec

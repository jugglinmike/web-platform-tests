import pytest
import urllib

import util.wd_assert as wd_assert

def inline(doc):
    return "data:text/html;charset=utf-8,%s" % urllib.quote(doc)

@pytest.fixture
def session(session):
    if session.session_id is None:
        session.start()
    return session

# 1. If the current top-level browsing context is no longer open, return error
#    with error code no such window.
def test_title_from_closed_context(session, switch_to_inactive):
    switch_to_inactive()

    result = session.send_raw_command("GET", "title")

    wd_assert.error(result, "no such window")

# 2. Handle any user prompts and return its value if it is an error.
def test_title_dismiss_dialog_alert(session, create_dialog):
    document = "<title>Dismisses`alert` dialog</title><h2>Hello</h2>"
    session.send_raw_command("POST", "url", dict(url=inline(document)))
    assert_handled = create_dialog('alert')

    result = session.send_raw_command("GET", "title")

    wd_assert.success(result, "Dismisses`alert` dialog")

    assert_handled(None)

def test_title_dismiss_dialog_prompt(session, create_dialog):
    document = "<title>Dismisses`prompt` dialog</title><h2>Hello</h2>"
    session.send_raw_command("POST", "url", dict(url=inline(document)))
    assert_handled = create_dialog('prompt')

    result = session.send_raw_command("GET", "title")

    wd_assert.success(result, "Dismisses`prompt` dialog")

    assert_handled(None)

def test_title_dismiss_dialog_confirm(session, create_dialog):
    document = "<title>Dismisses`confirm` dialog</title><h2>Hello</h2>"
    session.send_raw_command("POST", "url", dict(url=inline(document)))
    assert_handled = create_dialog('confirm')

    result = session.send_raw_command("GET", "title")

    wd_assert.success(result, "Dismisses`confirm` dialog")

    assert_handled(False)

# This test may produce a dialog that cannot be dismissed using the WebDriver
# protocol. In such cases, the session is effectively corrupted and all
# tests in this module that follow will fail spuriously.
#
# TODO: Research techniques for session isolation.
#def test_title_with_non_simple_dialog(session):
#    document = "<title>With non-simple dialog</title><h2>Hello</h2>"
#    spawn = """
#        var done = arguments[0];
#        setTimeout(function() {
#            done();
#            window.print();
#        }, 0);
#    """
#    session.send_raw_command("POST", "url", dict(url=inline(document)))
#    session.send_raw_command('POST', 'execute/async', dict(script=spawn, args=[]))
#
#    result = session.send_raw_command("GET", "title")
#    wd_assert.error(result, "unexpected alert open")

# 3. Let title be the initial value of the title IDL attribute of the current
#    top-level browsing context's active document.
def test_title_from_top_context(session):
    session.send_raw_command("POST", "url", dict(url=inline("<title>Foobar</title><h2>Hello</h2>")))
    result = session.send_raw_command("GET", "title")
    wd_assert.success(result, "Foobar")

def test_title_without_element(session):
    session.send_raw_command("POST", "url", dict(url=inline("<h2>Hello</h2>")))
    result = session.send_raw_command("GET", "title")
    wd_assert.success(result, "")

def test_title_after_modification(session):
    modify = "document.title = 'updated';"
    session.send_raw_command("POST", "url", dict(url=inline("<title>Initial</title><h2>Hello</h2>")))
    session.send_raw_command("POST", "execute/sync", dict(script=modify, args=[]))

    result = session.send_raw_command("GET", "title")

    wd_assert.success(result, "updated")

def test_title_strip_and_collapse(session):
    document = "<title>   a b\tc\nd\t \n e\t\n </title><h2>Hello</h2>"
    session.send_raw_command("POST", "url", dict(url=inline(document)))
    result = session.send_raw_command("GET", "title")
    wd_assert.success(result, "a b c d e")

def test_title_from_frame(session, switch_to_new_frame):
    session.send_raw_command("POST", "url", dict(url=inline("<title>Parent</title>parent")))

    switch_to_new_frame()
    switch_to_new_frame()

    result = session.send_raw_command("GET", "title")

    wd_assert.success(result, "Parent")

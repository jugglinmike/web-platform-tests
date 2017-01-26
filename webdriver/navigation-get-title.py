import pytest
import urllib

import util.wd_assert as wd_assert

def inline(doc):
    return "data:text/html;charset=utf-8,%s" % urllib.quote(doc)

# 1. If the current top-level browsing context is no longer open, return error
#    with error code no such window.
def test_title_from_closed_context(scommand, switch_to_inactive):
    switch_to_inactive()

    result = scommand("GET", "/title")

    wd_assert.error(result, "no such window")

# 2. Handle any user prompts and return its value if it is an error.
def test_title_dismiss_dialog_alert(scommand, create_dialog):
    document = "<title>Dismiss `alert` dialog</title><h2>Hello</h2>"
    scommand("POST", "/url", dict(url=inline(document)))
    create_dialog(dialog_type='alert', verify_dismissed=True)

    result = scommand("GET", "/title")

    wd_assert.success(result, "Dismiss `alert` dialog")

def test_title_dismiss_dialog_prompt(scommand, create_dialog):
    document = "<title>Dismiss `prompt` dialog</title><h2>Hello</h2>"
    scommand("POST", "/url", dict(url=inline(document)))
    create_dialog(dialog_type='prompt', verify_dismissed=True)

    result = scommand("GET", "/title")

    wd_assert.success(result, "Dismiss `prompt` dialog")

def test_title_dismiss_dialog_confirm(scommand, create_dialog):
    document = "<title>Dismiss `confirm` dialog</title><h2>Hello</h2>"
    scommand("POST", "/url", dict(url=inline(document)))
    create_dialog(dialog_type='confirm', verify_dismissed=True)

    result = scommand("GET", "/title")

    wd_assert.success(result, "Dismiss `confirm` dialog")

# This test may produce a dialog that cannot be dismissed using the WebDriver
# protocol. In such cases, the session is effectively corrupted and all
# tests in this module that follow will fail spuriously.
#
# TODO: Research techniques for session isolation.
#def test_title_with_non_simple_dialog(scommand):
#    document = "<title>With non-simple dialog</title><h2>Hello</h2>"
#    spawn = """
#        var done = arguments[0];
#        setTimeout(function() {
#            done();
#            window.print();
#        }, 0);
#    """
#    scommand("POST", "/url", dict(url=inline(document)))
#    scommand('POST', '/execute/async', dict(script=spawn, args=[]))
#
#    result = scommand("GET", "/title")
#    wd_assert.error(result, "unexpected alert open")

# 3. Let title be the initial value of the title IDL attribute of the current
#    top-level browsing context's active document.
def test_title_from_top_context(scommand):
    scommand("POST", "/url", dict(url=inline("<title>Foobar</title><h2>Hello</h2>")))
    result = scommand("GET", "/title")
    wd_assert.success(result, "Foobar")

def test_title_without_element(scommand):
    scommand("POST", "/url", dict(url=inline("<h2>Hello</h2>")))
    result = scommand("GET", "/title")
    wd_assert.success(result, "")

def test_title_after_modification(scommand):
    modify = "document.title = 'updated';"
    scommand("POST", "/url", dict(url=inline("<title>Initial</title><h2>Hello</h2>")))
    scommand("POST", "/execute/sync", dict(script=modify, args=[]))

    result = scommand("GET", "/title")

    wd_assert.success(result, "updated")

def test_title_strip_and_collapse(scommand):
    document = "<title>   a b\tc\nd\t \n e\t\n </title><h2>Hello</h2>"
    scommand("POST", "/url", dict(url=inline(document)))
    result = scommand("GET", "/title")
    wd_assert.success(result, "a b c d e")

def test_title_from_frame(scommand, switch_to_new_frame):
    scommand("POST", "/url", dict(url=inline("<title>Parent</title>parent")))

    switch_to_new_frame()
    switch_to_new_frame()

    result = scommand("GET", "/title")

    wd_assert.success(result, "Parent")

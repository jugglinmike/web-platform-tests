import httplib
import json
import pytest
import os
import urllib
from uuid import uuid4

import time

IS_GECKO = True

errors = {
    "element click intercepted": 400,
    "element not selectable": 400,
    "element not interactable": 400,
    "insecure certificate": 400,
    "invalid argument": 400,
    "invalid cookie domain": 400,
    "invalid coordinates": 400,
    "invalid element state": 400,
    "invalid selector": 400,
    "invalid session id": 404,
    "javascript error": 500,
    "move target out of bounds": 500,
    "no such alert": 400,
    "no such cookie": 404,
    "no such element": 404,
    "no such frame": 400,
    "no such window": 400,
    "script timeout": 408,
    "session not created": 500,
    "stale element reference": 400,
    "timeout": 408,
    "unable to set cookie": 500,
    "unable to capture screen": 500,
    "unexpected alert open": 500,
    "unknown command": 404,
    "unknown error": 500,
    "unknown method": 405,
    "unsupported operation": 500,
}

def inline(doc):
    return "data:text/html;charset=utf-8,%s" % urllib.quote(doc)

class Result():
    def __init__(self, response, validate):
        self.status = response.status
        self.body = response.read()

        if self.body:
            self.body = json.loads(self.body)

        # SpecID: dfn-send-a-response
        if validate:
            # > 3. Set the response's header with name and value with the following
            # >    values:
            # >
            # >    "Content-Type"
            # >       "application/json; charset=utf-8"
            # >    "cache-control"
            # >       "no-cache"
            assert response.getheader("Content-Type") == "application/json; charset=utf-8"
            assert response.getheader("cache-control") == "no-cache"

            # > 4. If data is not null, let response's body be a JSON Object with a
            #      key value set to the JSON Serialization of data.
            if self.body:
                assert "value" in self.body

        # Compatability shim for GeckoDriver
        #
        # TODO: Remove this when the following issue is resolved:
        # https://github.com/mozilla/webdriver-rust/issues/63
        if IS_GECKO and (not "value" in self.body or "sessionId" in self.body):
            self.body = { "value": self.body }

    def __str__(self):
        return 'Result(status=%d, body=%s)' % self.status, self.body

def request(
            host, port, method, path, req_body=None, headers=None,
            url_prefix=None, session_id=None,
            # TODO: Enable these assertions (GeckoDriver currently fails both)
            validate_response=False,
            ):
    if req_body is None and method == "POST":
        req_body = {}

    if isinstance(req_body, dict):
        req_body = json.dumps(req_body)

    if isinstance(req_body, unicode):
        req_body = req_body.encode("utf-8")

    if headers is None:
        headers = {}

    if not session_id is None:
        path = "/session/" + session_id + path

    if not url_prefix is None:
        path = "/" + url_prefix + path

    conn = httplib.HTTPConnection(host, port, strict=True)
    try:
        conn.request(method, path, req_body, headers)
        response = conn.getresponse()
    finally:
        conn.close()

    return Result(response, validate_response)

@pytest.fixture()
def command():
    host = 'localhost'
    port = os.environ["WD_PORT"]

    def command(*args, **kwargs):
        return request(host, port, *args, **kwargs)

    return command

@pytest.fixture()
def scommand(command, request):
    result = command("POST", "/session")
    assert result.status == 200
    assert "sessionId" in result.body["value"]
    session_id = result.body["value"]["sessionId"]

    def scommand(*args, **kwargs):
        if not "session_id" in kwargs:
            kwargs["session_id"] = session_id
        return command(*args, **kwargs)

    def delete_session():
        result = command("DELETE", "", session_id=session_id)
        assert result.status == 200
        assert result.body == None

    request.addfinalizer(delete_session)

    return scommand

@pytest.fixture()
def switch_to_inactive(scommand):
    def switch_to_inactive():
        initial = scommand("GET", "/window/handles").body["value"]

        result = scommand("POST",
                          "/execute/sync",
                          dict(script="window.open();", args=[]))
        assert result.status == 200

        with_new = scommand("GET", "/window/handles").body["value"]

        assert len(initial) == len(with_new) - 1

        new_handle = (set(with_new) - set(initial)).pop()

        result = scommand("POST", "/window", dict(handle=new_handle))

        assert result.status == 200

        scommand("DELETE", "/window")

    return switch_to_inactive

@pytest.fixture()
def switch_to_new_frame(scommand):
    def switch_to_new_frame():
        append = """
            var frame = document.createElement('iframe');
            document.body.appendChild(frame);
            return frame;
        """
        result = scommand("POST", "/execute/sync", dict(script=append, args=[]))
        assert result.status == 200
        result = scommand("POST", "/frame", dict(id=result.body["value"]))
        assert result.status == 200
    return switch_to_new_frame

@pytest.fixture()
def create_dialog(scommand, request):
    dismissed_values = {
        "alert": None,
        "prompt": None,
        "confirm": False
    }

    def create_dialog(dialog_type, verify_dismissed):
        dialog_id = str(uuid4())
        dismissed_value = dismissed_values[dialog_type]

        spawn = """
            var done = arguments[0];
            window.__WEBDRIVER = "initial value {0}";
            setTimeout(function() {{
                done(null);
                window.__WEBDRIVER = window.{1}("text {0}");
            }}, 0);
        """.format(dialog_id, dialog_type)

        scommand('POST', '/execute/async', dict(script=spawn, args=[]))

        def verify():
            result = scommand('GET', '/alert/text')

            # If there were any existing dialogs prior to the creation of this
            # fixture's dialog, then the "Get Alert Text" command will return
            # successfully. In that case, the text must be different than that of
            # this fixture's dialog.
            try:
                assert_error(result, 'no such alert')
            except:
                assert result.status == 200
                assert result.body["value"] != "text {0}".format(dialog_id)

            probe = 'return window.__WEBDRIVER;'
            result = scommand('POST', '/execute/sync', dict(script=probe, args=[]))
            assert result.status == 200
            assert result.body["value"] == dismissed_value, "Dialog was dismissed, not accepted"

        if verify_dismissed:
            request.addfinalizer(verify)

    return create_dialog

def assert_error(result, name):
    assert result.status == errors[name]
    assert result.body["value"]["error"] == name
    assert isinstance(result.body["value"]["message"], basestring)
    if not IS_GECKO:
        assert isinstance(result.body["value"]["stacktrace"], basestring)

# 1. If the current top-level browsing context is no longer open, return error
#    with error code no such window.
def test_title_from_closed_context(scommand, switch_to_inactive):
    switch_to_inactive()
    result = scommand("GET", "/title")
    assert_error(result, "no such window")

# 2. Handle any user prompts and return its value if it is an error.
def test_title_dismiss_dialog_alert(scommand, create_dialog):
    document = "<title>Dismiss `alert` dialog</title><h2>Hello</h2>"
    scommand("POST", "/url", dict(url=inline(document)))
    create_dialog(dialog_type='alert', verify_dismissed=True)

    result = scommand("GET", "/title")
    assert result.status == 200
    assert result.body["value"] == "Dismiss `alert` dialog"

def test_title_dismiss_dialog_prompt(scommand, create_dialog):
    document = "<title>Dismiss `prompt` dialog</title><h2>Hello</h2>"
    scommand("POST", "/url", dict(url=inline(document)))
    create_dialog(dialog_type='prompt', verify_dismissed=True)

    result = scommand("GET", "/title")
    assert result.status == 200
    assert result.body["value"] == "Dismiss `prompt` dialog"

def test_title_dismiss_dialog_confirm(scommand, create_dialog):
    document = "<title>Dismiss `confirm` dialog</title><h2>Hello</h2>"
    scommand("POST", "/url", dict(url=inline(document)))
    create_dialog(dialog_type='confirm', verify_dismissed=True)

    result = scommand("GET", "/title")
    assert result.status == 200
    assert result.body["value"] == "Dismiss `confirm` dialog"

def test_title_with_non_simple_dialog(scommand):
    document = "<title>With non-simple dialog</title><h2>Hello</h2>"
    spawn = """
        var done = arguments[0];
        setTimeout(function() {
            done();
            window.print();
        }, 0);
    """
    scommand("POST", "/url", dict(url=inline(document)))
    scommand('POST', '/execute/async', dict(script=spawn, args=[]))

    time.sleep(4)

    result = scommand("GET", "/title")
    assert_error(result, "unexpected alert open")

# 3. Let title be the initial value of the title IDL attribute of the current
#    top-level browsing context's active document.
def test_title_from_top_context(scommand):
    scommand("POST", "/url", dict(url=inline("<title>Foobar</title><h2>Hello</h2>")))
    result = scommand("GET", "/title")
    assert result.status == 200
    assert result.body["value"] == "Foobar"

def test_title_without_element(scommand):
    scommand("POST", "/url", dict(url=inline("<h2>Hello</h2>")))
    result = scommand("GET", "/title")
    assert result.status == 200
    assert result.body["value"] == ""

def test_title_from_frame(scommand, switch_to_new_frame):
    scommand("POST", "/url", dict(url=inline("<title>Parent</title>parent")))

    switch_to_new_frame()
    switch_to_new_frame()

    result = scommand("GET", "/title")

    assert result.status == 200
    assert result.body["value"] == "Parent"

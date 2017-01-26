from uuid import uuid4

import pytest

from util.assert_error import assert_error
from util.request import request

@pytest.fixture()
def command(session):
    host = session.transport.host
    port = session.transport.port

    def command(*args, **kwargs):
        return request(host, port, *args, **kwargs)

    return command

@pytest.fixture()
def scommand(command, session):
    if not session.session_id:
        session.start()

    def scommand(*args, **kwargs):
        if not "session_id" in kwargs:
            kwargs["session_id"] = session.session_id
        return command(*args, **kwargs)

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

from uuid import uuid4

import pytest

import util.wd_assert as wd_assert
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
    """Create a new browsing context, switch to that new context, and then
    delete the context."""
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
def create_dialog(scommand):
    """Create a dialog (one of "alert", "prompt", or "confirm") and provide a
    function to validate that a the dialog has been "handled" (either accepted
    or dismissed) by returning some value."""

    def create_dialog(dialog_type):
        dialog_id = str(uuid4())
        dialog_text = "text " + dialog_id

        # Script completion and modal summoning are scheduled on two separate
        # turns of the event loop to ensure that both occur regardless of how
        # the user agent manages script execution.
        spawn = """
            var done = arguments[0];
            window.__WEBDRIVER = "initial value {0}";
            setTimeout(function() {{
                done();
            }}, 0);
            setTimeout(function() {{
                window.__WEBDRIVER = window.{1}("{2}");
            }}, 0);
        """.format(dialog_id, dialog_type, dialog_text)

        result = scommand('POST', '/execute/async', dict(script=spawn, args=[]))
        assert result.status == 200

        def assert_handled(expected_value):
            result = scommand('GET', '/alert/text')

            # If there were any existing dialogs prior to the creation of this
            # fixture's dialog, then the "Get Alert Text" command will return
            # successfully. In that case, the text must be different than that of
            # this fixture's dialog.
            try:
                wd_assert.error(result, 'no such alert')
            except:
                assert result.status == 200 and result.body["value"] != dialog_text, \
                    "Dialog was not handled."

            probe = 'return window.__WEBDRIVER;'
            result = scommand('POST', '/execute/sync', dict(script=probe, args=[]))

            assert result.status == 200, \
                "Unable to verify that dialog was handled with expected value"
            assert result.body["value"] == expected_value, \
                "Dialog was not handled with expected value"

        return assert_handled

    return create_dialog

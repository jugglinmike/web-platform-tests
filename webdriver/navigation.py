import json
import pytest
import types

import webdriver

from util.inline import inline
from util import wd_assert

alert_doc = inline("<script>window.alert()</script>")
frame_doc = inline("<p>frame")
one_frame_doc = inline("<iframe src='%s'></iframe>" % frame_doc)
two_frames_doc = inline("<iframe src='%s'></iframe>" % one_frame_doc)


# TODO(ato): 7.1 Get


def test_get_current_url_no_browsing_context(session, create_window):
    # 7.2 step 1
    session.window_handle = create_window()
    session.close()

    result = session.send_raw_command("GET", "url")

    wd_assert.error(result, "no such window")


def test_get_current_url_alert_prompt(session):
    # 7.2 step 2
    session.url = alert_doc

    result = session.send_raw_command("GET", "url")

    wd_assert.success(result, alert_doc)

def test_get_current_url_matches_location(session):
    # 7.2 step 3
    url = session.execute_script("return window.location.href")
    assert session.url == url

def test_get_current_url_payload(session):
    # 7.2 step 4-5
    session.start()

    result = session.send_raw_command("GET", "url")

    assert result.status == 200
    assert isinstance(result.body["value"], basestring)

def test_get_current_url_special_pages(session):
    session.url = "about:blank"

    result = session.send_raw_command("GET", "url")

    wd_assert.success(result, "about:blank")

# TODO(ato): This test requires modification to pass on Windows
def test_get_current_url_file_protocol(session):
    import os
    if "WD_GECKO" in os.environ:
        return
    # tests that the browsing context remains the same
    # when navigated privileged documents
    session.url = "file:///"

    result = session.send_raw_command("GET", "url")

    wd_assert.success(result, "file:///")

# TODO(ato): Test for http:// and https:// protocols.
# We need to expose a fixture for accessing
# documents served by wptserve in order to test this.

def test_get_current_url_after_modified_location(session):
    session.execute_script("window.location.href = 'about:blank#wd_test_modification'")

    result = session.send_raw_command("GET", "url")

    wd_assert.success(result, "about:blank#wd_test_modification")

def test_get_current_url_nested_browsing_context(session, create_frame):
    session.url = "about:blank#wd_from_within_frame"

    session.send_command("POST", "frame", dict(id=create_frame()))

    result = session.send_raw_command("GET", "url")

    wd_assert.success(result, "about:blank#wd_from_within_frame")

def test_get_current_url_nested_browsing_contexts(session):
    session.url = two_frames_doc
    top_level_url = session.url

    outer_frame = session.find.css("iframe", all=False)
    session.switch_frame(outer_frame)

    inner_frame = session.find.css("iframe", all=False)
    session.switch_frame(inner_frame)

    assert session.url == top_level_url

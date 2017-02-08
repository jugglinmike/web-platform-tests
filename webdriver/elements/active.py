import pytest
import urllib

def inline(doc):
    return "data:text/html;charset=utf-8,%s" % urllib.quote(doc)

WEB_ELEMENT_IDENTIFIER = "element-6066-11e4-a52e-4f735466cecf"

def assert_is_element(value):
    assert isinstance(value, dict)
    assert WEB_ELEMENT_IDENTIFIER in value

@pytest.fixture()
def session(session):
    session.start()
    return session

@pytest.fixture()
def get_id(session):
    def get_id(element):
        assert_is_element(element)

        return session.send_raw_command("GET", "element/%s/attribute/id" % element[WEB_ELEMENT_IDENTIFIER])
    return get_id

# > 3. Let active element be the active element of the current browsing
#      context’s document element.
# > 4. Let active web element be the JSON Serialization of active element.
# > 5. Return success with data active web element.
def test_sucess_document(session, get_id):
    session.url = inline("""
        <body id="document-body">
            <h1>Heading</h1>
            <input id="the-input" />
            <input id="interactable-input" />
            <input id="non-interactable-input" style="opacity: 0;" />
            <p>Another element</p>
        </body>""")
    result = session.send_raw_command("GET", "element/active")

    assert result.status == 200
    assert_is_element(result.body["value"])

    result = get_id(result.body["value"])

    assert result.status == 200
    assert result.body["value"] == "document-body"

def test_sucess_input(session, get_id):
    session.url = inline("""
        <body id="document-body">
            <h1>Heading</h1>
            <input id="interactable-input" autofocus />
            <input id="non-interactable-input" style="opacity: 0;" />
            <p>Another element</p>
        </body>""")
    result = session.send_raw_command("GET", "element/active")

    assert result.status == 200
    assert_is_element(result.body["value"])

    result = get_id(result.body["value"])

    assert result.status == 200
    assert result.body["value"] == "interactable-input"

def test_sucess_input_non_interactable(session, get_id):
    session.url = inline("""
        <body id="document-body">
            <h1>Heading</h1>
            <input id="interactable-input" />
            <input id="non-interactable-input" style="opacity: 0;" autofocus />
            <p>Another element</p>
        </body>""")
    result = session.send_raw_command("GET", "element/active")

    assert result.status == 200
    assert_is_element(result.body["value"])

    result = get_id(result.body["value"])

    assert result.status == 200
    assert result.body["value"] == "non-interactable-input"

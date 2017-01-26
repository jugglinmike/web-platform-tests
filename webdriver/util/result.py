import json
import os

def validate_response(response):
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

class Result():
    def __init__(self, response, validate):
        self.status = response.status
        self.body = response.read()

        if self.body:
            self.body = json.loads(self.body)

        # SpecID: dfn-send-a-response
        if validate:
            validate_response(response)

        # Compatability shim for GeckoDriver
        #
        # TODO: Remove this when the following issue is resolved:
        # https://github.com/mozilla/webdriver-rust/issues/63
        if ("WD_GECKO" in os.environ) and (not "value" in self.body or "sessionId" in self.body):
            self.body = { "value": self.body }

    def __repr__(self):
        return 'Result(status=%d, body=%s)' % (self.status, self.body)

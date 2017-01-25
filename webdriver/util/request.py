import httplib
import json
from result import Result

def request(
            host, port, method, path, req_body=None, headers=None,
            url_prefix=None, session_id=None, validate_response=False,
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

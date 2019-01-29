"""app: handle requests."""

import json

from lambda_proxy.proxy import API

APP = API(app_name="app")


@APP.route("/", methods=["GET"], cors=True)
def main():
    """Return JSON Object."""
    return ("OK", "text/plain", "Yo")


@APP.route("/json", methods=["GET"], cors=True)
def json_handler():
    """Return JSON Object."""
    return ("OK", "application/json", json.dumps({"app": "it works"}))


@APP.route("/binary", methods=["GET"], cors=True, payload_compression_method="gzip")
def bin():
    """Return image."""
    with open("./rpix.png", "rb") as f:
        return ("OK", "image/png", f.read())


@APP.route(
    "/b64binary",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
def b64bin():
    """Return base64 encoded image."""
    with open("./rpix.png", "rb") as f:
        return ("OK", "image/png", f.read())

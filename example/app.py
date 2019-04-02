"""app: handle requests."""

from typing import Tuple, io

import json

from lambda_proxy.proxy import API

APP = API(name="app")


@APP.route("/", methods=["GET"], cors=True)
def main() -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", "Yo")


@APP.route("/<string:user>", methods=["GET"], cors=True)
@APP.route("/<string:user>/<int:num>", methods=["GET"], cors=True)
def double(user: str, num: int = 0) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", f"{user}-{num}")


@APP.route("/json", methods=["GET"], cors=True)
def json_handler() -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "application/json", json.dumps({"app": "it works"}))


@APP.route("/binary", methods=["GET"], cors=True, payload_compression_method="gzip")
def bin() -> Tuple[str, str, io.BinaryIO]:
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
def b64bin() -> Tuple[str, str, io.BinaryIO]:
    """Return base64 encoded image."""
    with open("./rpix.png", "rb") as f:
        return ("OK", "image/png", f.read())


@APP.route("/openapi.json", methods=["GET"], cors=True)
def doc() -> Tuple[str, str, io.BinaryIO]:
    """Return json docs."""
    doc = APP._get_openapi()
    return ("OK", "application/json", json.dumps(doc))

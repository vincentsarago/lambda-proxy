"""app: handle requests."""

from typing import Dict, Tuple, io

import json

from lambda_proxy.proxy import API

APP = API(name="app")


@APP.route("/", methods=["GET"], cors=True)
def main() -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", "Yo")


@APP.route("/<regex([0-9]{2}-[a-zA-Z]{5}):regex1>", methods=["GET"], cors=True)
def _re_one(regex1: str) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", input)


@APP.route("/<regex([0-9]{1}-[a-zA-Z]{5}):regex2>", methods=["GET"], cors=True)
def _re_two(regex2: str) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", input)


@APP.route("/add", methods=["GET", "POST"], cors=True)
def post(body) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", body)


@APP.route("/<string:user>", methods=["GET"], cors=True)
@APP.route("/<string:user>/<int:num>", methods=["GET"], cors=True)
def double(user: str, num: int = 0) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", f"{user}-{num}")


@APP.route("/kw/<string:user>", methods=["GET"], cors=True)
def kw_method(user: str, **kwargs: Dict) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", f"{user}")


@APP.route("/ctx/<string:user>", methods=["GET"], cors=True)
@APP.pass_context
@APP.pass_event
def ctx_method(evt: Dict, ctx: Dict, user: str, num: int = 0) -> Tuple[str, str, str]:
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

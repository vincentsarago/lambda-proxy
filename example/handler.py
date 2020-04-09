"""app: handle requests."""

from typing import Dict, Tuple
import typing.io

import json

from lambda_proxy.proxy import API

app = API(name="app", debug=True)


@app.get("/", cors=True)
def main() -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", "Yo")


@app.get("/<regex([0-9]{2}-[a-zA-Z]{5}):regex1>", cors=True)
def _re_one(regex1: str) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", regex1)


@app.get("/<regex([0-9]{1}-[a-zA-Z]{5}):regex2>", cors=True)
def _re_two(regex2: str) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", regex2)


@app.post("/people", cors=True)
def people_post(body) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", body)


@app.get("/people", cors=True)
def people_get() -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", "Nope")


@app.get("/<string:user>", cors=True)
@app.get("/<string:user>/<int:num>", cors=True)
def double(user: str, num: int = 0) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", f"{user}-{num}")


@app.get("/kw/<string:user>", cors=True)
def kw_method(user: str, **kwargs: Dict) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", f"{user}")


@app.get("/ctx/<string:user>", cors=True)
@app.pass_context
@app.pass_event
def ctx_method(evt: Dict, ctx: Dict, user: str, num: int = 0) -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "text/plain", f"{user}-{num}")


@app.get("/json", cors=True)
def json_handler() -> Tuple[str, str, str]:
    """Return JSON Object."""
    return ("OK", "application/json", json.dumps({"app": "it works"}))


@app.get("/binary", cors=True, payload_compression_method="gzip")
def bin() -> Tuple[str, str, typing.io.BinaryIO]:
    """Return image."""
    with open("./rpix.png", "rb") as f:
        return ("OK", "image/png", f.read())


@app.get(
    "/b64binary", cors=True, payload_compression_method="gzip", binary_b64encode=True,
)
def b64bin() -> Tuple[str, str, typing.io.BinaryIO]:
    """Return base64 encoded image."""
    with open("./rpix.png", "rb") as f:
        return ("OK", "image/png", f.read())

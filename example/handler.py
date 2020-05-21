"""app: handle requests."""

from typing import Dict

from lambda_proxy.proxy import API
from lambda_proxy.responses import PlainTextResponse, Response

app = API(name="app")


@app.get("/", cors=True, response_class=PlainTextResponse)
def main():
    """Return String."""
    return "Yo"


@app.post("/people", cors=True, response_class=PlainTextResponse)
def people_post(body):
    """Return String."""
    return body


@app.get("/people", cors=True, response_class=PlainTextResponse)
def people_get():
    """Return String."""
    return "Nope"


@app.get("/kw/<string:user>", cors=True, response_class=PlainTextResponse)
def kw_method(user: str, **kwargs: Dict):
    """Return String."""
    return f"{user}"


@app.get("/ctx/<string:user>", cors=True, response_class=PlainTextResponse)
@app.pass_context
@app.pass_event
def ctx_method(evt: Dict, ctx: Dict, user: str, num: int = 0):
    """Return String."""
    return f"{user}-{num}"


@app.get("/json/itworks", cors=True)
def json_handler():
    """Return JSON Object."""
    return {"app": "it works"}


@app.get("/binary", cors=True, payload_compression_method="gzip")
def bin():
    """Return image."""
    with open("./rpix.png", "rb") as f:
        return Response(f.read(), media_type="image/png")


@app.get(
    "/b64binary", cors=True, payload_compression_method="gzip", binary_b64encode=True,
)
def b64bin():
    """Return base64 encoded image."""
    with open("./rpix.png", "rb") as f:
        return Response(f.read(), media_type="image/png")


@app.get("/header/json", cors=True)
def addHeader_handler(resp: Response):
    """Return JSON Object."""
    resp.headers["Cache-Control"] = "max-age=3600"
    return {"app": "it works"}


@app.get("/<string:user>", cors=True, response_class=PlainTextResponse)
@app.get("/<string:user>/<int:num>", cors=True, response_class=PlainTextResponse)
def double(user: str, num: int = 0):
    """Return String."""
    return f"{user}-{num}"


@app.get(
    "/<regex([0-9]{2}-[a-zA-Z]{5}):regex1>", cors=True, response_class=PlainTextResponse
)
def _re_one(regex1: str):
    """Return String."""
    return regex1


@app.get(
    "/<regex([0-9]{1}-[a-zA-Z]{5}):regex2>", cors=True, response_class=PlainTextResponse
)
def _re_two(regex2: str):
    """Return String."""
    return regex2

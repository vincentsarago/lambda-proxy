"""Test lambda-proxy."""

import json
import zlib
import base64

import pytest
from mock import Mock

from lambda_proxy.proxy import RouteEntry, API


funct = Mock(__name__="Mock")


def test_RouteEntry_default():
    """Should work as expected."""
    route = RouteEntry(funct, "my-function", "/endpoint/test/<id>")
    assert route.view_function == funct
    assert route.view_name == "my-function"
    assert route.methods == ["GET"]
    # assert route.view_args == []
    assert not route.cors
    assert not route.token
    assert not route.compression
    assert not route.b64encode


def test_RouteEntry_Options():
    """Should work as expected."""
    route = RouteEntry(
        funct,
        "my-function",
        "/endpoint/test/<id>",
        ["POST"],
        cors=True,
        token="Yo",
        payload_compression_method="deflate",
        binary_b64encode=True,
    )
    assert route.view_function == funct
    assert route.view_name == "my-function"
    assert route.methods == ["POST"]
    # assert route.view_args == []
    assert route.cors
    assert route.token == "Yo"
    assert route.compression == "deflate"
    assert route.b64encode


def test_RouteEntry_invalidCompression():
    """Should work as expected."""
    with pytest.raises(ValueError):
        RouteEntry(
            funct,
            "my-function",
            "/endpoint/test/<id>",
            payload_compression_method="nope",
        )


def test_API_init():
    """Should work as expected."""
    app = API(app_name="test")
    assert app.app_name == "test"
    assert not app.routes
    assert not app.debug
    assert app.log.getEffectiveLevel() == 40  # ERROR

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_noLog():
    """Should work as expected."""
    app = API(app_name="test", configure_logs=False)
    assert app.app_name == "test"
    assert not app.routes
    assert not app.debug
    assert app.log

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_logDebug():
    """Should work as expected."""
    app = API(app_name="test", debug=True)
    assert app.log.getEffectiveLevel() == 10  # DEBUG

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_addRoute():
    """Add and parse route."""
    app = API(app_name="test")
    assert not app.routes

    app._add_route("/endpoint/test/<id>", funct, methods=["GET"], cors=True, token="yo")
    assert app.routes

    with pytest.raises(ValueError):
        app._add_route("/endpoint/test/<id>", funct, methods=["GET"], cors=True)

    with pytest.raises(TypeError):
        app._add_route("/endpoint/test/<id>", funct, methods=["GET"], c=True)

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API():
    """Add and parse route."""
    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<user>", funct, methods=["GET"], cors=True)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with("remotepixel")


def test_querystringNull():
    """Add and parse route."""
    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<user>", funct, methods=["GET"], cors=True)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": None,
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with("remotepixel")


def test_headersNull():
    """Add and parse route."""
    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<user>", funct, methods=["GET"], cors=True)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": None,
        "queryStringParameters": {},
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with("remotepixel")


def test_API_encoding():
    """Test b64 encoding."""
    app = API(app_name="test")

    body = b"thisisafakeencodedjpeg"
    b64body = base64.b64encode(body).decode()

    funct = Mock(__name__="Mock", return_value=("OK", "image/jpeg", body))
    app._add_route("/test/<user>.jpg", funct, methods=["GET"], cors=True)

    event = {
        "path": "/test/remotepixel.jpg",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": body,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "image/jpeg",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp

    app._add_route(
        "/test_encode/<user>.jpg",
        funct,
        methods=["GET"],
        cors=True,
        binary_b64encode=True,
    )
    event = {
        "path": "/test_encode/remotepixel.jpg",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": b64body,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "image/jpeg",
        },
        "isBase64Encoded": True,
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp


def test_API_compression():
    """Test compression and base64."""
    body = b"thisisafakeencodedjpeg"
    gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
    gzbody = gzip_compress.compress(body) + gzip_compress.flush()
    b64gzipbody = base64.b64encode(gzbody).decode()

    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "image/jpeg", body))
    app._add_route(
        "/test_compress/<user>.jpg",
        funct,
        methods=["GET"],
        cors=True,
        payload_compression_method="gzip",
    )

    # Should compress because "Accept-Encoding" is in header
    event = {
        "path": "/test_compress/remotepixel.jpg",
        "httpMethod": "GET",
        "headers": {"Accept-Encoding": "gzip, deflate"},
        "queryStringParameters": {},
    }
    resp = {
        "body": gzbody,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Encoding": "gzip",
            "Content-Type": "image/jpeg",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp

    # Should not compress because "Accept-Encoding" is missing in header
    event = {
        "path": "/test_compress/remotepixel.jpg",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": body,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "image/jpeg",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp

    # Should compress and encode to base64
    app._add_route(
        "/test_compress_b64/<user>.jpg",
        funct,
        methods=["GET"],
        cors=True,
        payload_compression_method="gzip",
        binary_b64encode=True,
    )
    event = {
        "path": "/test_compress_b64/remotepixel.jpg",
        "httpMethod": "GET",
        "headers": {"Accept-Encoding": "gzip, deflate"},
        "queryStringParameters": {},
    }
    resp = {
        "body": b64gzipbody,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Encoding": "gzip",
            "Content-Type": "image/jpeg",
        },
        "isBase64Encoded": True,
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp

    funct = Mock(
        __name__="Mock",
        return_value=("OK", "application/json", json.dumps({"test": 0})),
    )
    # Should compress and encode to base64
    app._add_route(
        "/test_compress_b64/<user>.json",
        funct,
        methods=["GET"],
        cors=True,
        payload_compression_method="gzip",
        binary_b64encode=True,
    )
    event = {
        "path": "/test_compress_b64/remotepixel.json",
        "httpMethod": "GET",
        "headers": {"Accept-Encoding": "gzip, deflate"},
        "queryStringParameters": {},
    }

    body = bytes(json.dumps({"test": 0}), "utf-8")
    gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
    gzbody = gzip_compress.compress(body) + gzip_compress.flush()
    b64gzipbody = base64.b64encode(gzbody).decode()
    resp = {
        "body": b64gzipbody,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Encoding": "gzip",
            "Content-Type": "application/json",
        },
        "isBase64Encoded": True,
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/test_compress_b64/remotepixel.json",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }

    resp = {
        "body": json.dumps({"test": 0}),
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp


def test_API_otherCompression():
    """Test other compression."""

    body = b"thisisafakeencodedjpeg"
    zlib_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)
    deflate_compress = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    zlibbody = zlib_compress.compress(body) + zlib_compress.flush()
    deflbody = deflate_compress.compress(body) + deflate_compress.flush()

    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "image/jpeg", body))
    app._add_route(
        "/test_deflate/<user>.jpg",
        funct,
        methods=["GET"],
        cors=True,
        payload_compression_method="deflate",
    )
    app._add_route(
        "/test_zlib/<user>.jpg",
        funct,
        methods=["GET"],
        cors=True,
        payload_compression_method="zlib",
    )

    # Zlib
    event = {
        "path": "/test_zlib/remotepixel.jpg",
        "httpMethod": "GET",
        "headers": {"Accept-Encoding": "zlib, gzip, deflate"},
        "queryStringParameters": {},
    }
    resp = {
        "body": zlibbody,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Encoding": "zlib",
            "Content-Type": "image/jpeg",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp

    # Deflate
    event = {
        "path": "/test_deflate/remotepixel.jpg",
        "httpMethod": "GET",
        "headers": {"Accept-Encoding": "zlib, gzip, deflate"},
        "queryStringParameters": {},
    }
    resp = {
        "body": deflbody,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Encoding": "deflate",
            "Content-Type": "image/jpeg",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp


def test_API_routeURL():
    """Should catch invalid route and parse valid args."""
    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<user>", funct, methods=["GET"], cors=True)

    event = {
        "route": "/users/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": '{"errorMessage": "Missing route parameter"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": 400,
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/users/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": '{"errorMessage": "No view function for: /users/remotepixel"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": 400,
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "POST",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": '{"errorMessage": "Unsupported method: POST"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": 400,
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/users/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": '{"errorMessage": "No view function for: /users/remotepixel"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": 400,
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/test/users/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": '{"errorMessage": "No view function for: /test/users/remotepixel"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": 400,
    }
    res = app(event, {})
    assert res == resp

    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route(
        "/test/<string:v>/<uuid:uuid>/<int:z>/<float:x>.<ext>",
        funct,
        methods=["GET"],
        cors=True,
    )

    event = {
        "path": "/test/remotepixel/6b0d1f74-8f81-11e8-83fd-6a0003389b00/1/-1.0.jpeg",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with(
        "remotepixel", "6b0d1f74-8f81-11e8-83fd-6a0003389b00", 1, -1.0, "jpeg"
    )

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_routeToken(monkeypatch):
    """Validate tokens."""
    monkeypatch.setenv("TOKEN", "yo")

    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<user>", funct, methods=["GET"], cors=True, token=True)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {"access_token": "yo"},
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with("remotepixel")

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {"inp": 1, "access_token": "yo"},
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with("remotepixel", inp=1)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {"access_token": "yep"},
    }
    resp = {
        "body": '{"message": "Invalid access token"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": 500,
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {"token": "yo"},
    }
    resp = {
        "body": '{"message": "Invalid access token"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": 500,
    }
    res = app(event, {})
    assert res == resp

    monkeypatch.delenv("TOKEN", raising=False)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {"access_token": "yo"},
    }
    resp = {
        "body": '{"message": "Invalid access token"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": 500,
    }
    res = app(event, {})
    assert res == resp

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_functionError():
    """Add and parse route."""
    app = API(app_name="test")
    funct = Mock(__name__="Mock", side_effect=Exception("hey something went wrong"))
    app._add_route("/test/<user>", funct, methods=["GET"], cors=True)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": '{"errorMessage": "hey something went wrong"}',
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "statusCode": 500,
    }
    res = app(event, {})
    assert res == resp

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_Post():
    """SHould work as expected on POST request."""
    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<user>", funct, methods=["GET", "POST"], cors=True)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "POST",
        "headers": {},
        "queryStringParameters": {},
        "body": b"0001",
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET,POST",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with("remotepixel", body=b"0001")

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET,POST",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with("remotepixel")

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_ctx():
    """Should work as expected and pass ctx and evt to the function."""
    app = API(app_name="test")

    @app.route("/<id>", methods=["GET"], cors=True)
    @app.pass_event
    @app.pass_context
    def print_id(ctx, evt, id, params=None):
        return (
            "OK",
            "application/json",
            {"ctx": ctx, "evt": evt, "id": id, "params": params},
        )

    event = {
        "path": "/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {"params": "1"},
    }
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    res = app(event, {"ctx": "jqtrde"})
    body = res["body"]
    assert res["headers"] == headers
    assert res["statusCode"] == 200
    assert body["id"] == "remotepixel"
    assert body["params"] == "1"
    assert body["evt"] == event
    assert body["ctx"] == {"ctx": "jqtrde"}

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)

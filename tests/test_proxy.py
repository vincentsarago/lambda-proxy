"""Test lambda-proxy."""

from typing import Dict, Tuple

import os
import json
import zlib
import base64

import pytest
from mock import Mock

from lambda_proxy import proxy

json_api = os.path.join(os.path.dirname(__file__), "fixtures", "openapi.json")
with open(json_api, "r") as f:
    openapi_content = json.loads(f.read())

json_api_custom = os.path.join(
    os.path.dirname(__file__), "fixtures", "openapi_custom.json"
)
with open(json_api_custom, "r") as f:
    openapi_custom_content = json.loads(f.read())

json_apigw = os.path.join(os.path.dirname(__file__), "fixtures", "openapi_apigw.json")
with open(json_apigw, "r") as f:
    openapi_apigw_content = json.loads(f.read())

funct = Mock(__name__="Mock")


def test_value_converters():
    """Convert convert value to correct type."""
    pathArg = "<string:v>"
    assert "123" == proxy._converters("123", pathArg)

    pathArg = "<int:v>"
    assert 123 == proxy._converters("123", pathArg)

    pathArg = "<float:v>"
    assert 123.0 == proxy._converters("123", pathArg)

    pathArg = "<uuid:v>"
    assert "f5c21e12-8317-11e9-bf96-2e2ca3acb545" == proxy._converters(
        "f5c21e12-8317-11e9-bf96-2e2ca3acb545", pathArg
    )

    pathArg = "<v>"
    assert "123" == proxy._converters("123", pathArg)


def test_path_to_regex_convert():
    """Convert route path to regex."""
    path = "/jqtrde/<a>/<string:path>/<int:num>/<float:fl>/<uuid:id>/<regex([A-Z0-9]{5}):var>/<regex([a-z]{1}):othervar>"
    assert (
        "^/jqtrde/([a-zA-Z0-9_]+)/([a-zA-Z0-9_]+)/([0-9]+)/([+-]?[0-9]+.[0-9]+)/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/([A-Z0-9]{5})/([a-z]{1})$"
        == proxy._path_to_regex(path)
    )


def test_path_to_openapi_converters():
    """Convert proxy path to openapi path."""
    path = "/<string:num>/<test>-<regex([0-1]{4}):var>"
    assert "/{num}/{test}-{var}" == proxy._path_to_openapi(path)


def test_RouteEntry_default():
    """Should work as expected."""
    route = proxy.RouteEntry(funct, "/endpoint/test/<id>")
    assert route.endpoint == funct
    assert route.methods == ["GET"]
    assert not route.cors
    assert not route.token
    assert not route.compression
    assert not route.b64encode


def test_RouteEntry_Options():
    """Should work as expected."""
    route = proxy.RouteEntry(
        funct,
        "/endpoint/test/<id>",
        ["POST"],
        cors=True,
        token="Yo",
        payload_compression_method="deflate",
        binary_b64encode=True,
    )
    assert route.endpoint == funct
    assert route.methods == ["POST"]
    assert route.cors
    assert route.token == "Yo"
    assert route.compression == "deflate"
    assert route.b64encode


def test_RouteEntry_invalidCompression():
    """Should work as expected."""
    with pytest.raises(ValueError):
        proxy.RouteEntry(
            funct,
            "my-function",
            "/endpoint/test/<id>",
            payload_compression_method="nope",
        )


def test_API_init():
    """Should work as expected."""
    app = proxy.API(name="test")
    assert app.name == "test"
    assert len(list(app.routes.keys())) == 3
    assert not app.debug
    assert app.log.getEffectiveLevel() == 40  # ERROR

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_noDocs():
    """Do not set default documentation routes."""
    app = proxy.API(name="test", add_docs=False)
    assert app.name == "test"
    assert len(list(app.routes.keys())) == 0
    assert not app.debug
    assert app.log.getEffectiveLevel() == 40  # ERROR

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_noLog():
    """Should work as expected."""
    app = proxy.API(name="test", configure_logs=False)
    assert app.name == "test"
    assert not app.debug
    assert app.log

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_logDebug():
    """Should work as expected."""
    app = proxy.API(name="test", debug=True)
    assert app.log.getEffectiveLevel() == 10  # DEBUG

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_addRoute():
    """Add and parse route."""
    app = proxy.API(name="test")
    assert len(list(app.routes.keys())) == 3

    app._add_route("/endpoint/test/<id>", funct, methods=["GET"], cors=True, token="yo")
    assert app.routes

    with pytest.raises(ValueError):
        app._add_route("/endpoint/test/<id>", funct, methods=["GET"], cors=True)

    with pytest.raises(TypeError):
        app._add_route("/endpoint/test/<id>", funct, methods=["GET"], c=True)

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_proxy_API():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<string:user>/<name>", funct, methods=["GET"], cors=True)

    event = {
        "path": "/test/remote/pixel",
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
    funct.assert_called_with(user="remote", name="pixel")


def test_proxy_intStatus_API():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=(204, "text/plain", "heyyyy"))
    app._add_route("/test", funct, methods=["GET"], cors=True)

    event = {
        "path": "/test",
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
        "statusCode": 204,
    }
    res = app(event, {})
    assert res == resp


def test_proxy_APIpath():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<string:user>/<name>", funct, methods=["GET"], cors=True)

    event = {
        "resource": "/",
        "path": "/test/remote/pixel",
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
    funct.assert_called_with(user="remote", name="pixel")


def test_proxy_APIpathProxy():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<string:user>/<name>", funct, methods=["GET"], cors=True)

    event = {
        "resource": "{something+}",
        "pathParameters": {"something": "test/remote/pixel"},
        "path": "/test/remote/pixel",
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
    funct.assert_called_with(user="remote", name="pixel")


def test_proxy_APIpathCustomDomain():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<string:user>/<name>", funct, methods=["GET"], cors=True)

    event = {
        "resource": "/{something+}",
        "pathParameters": {"something": "test/remote/pixel"},
        "path": "/myapi/test/remote/pixel",
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
    funct.assert_called_with(user="remote", name="pixel")


def test_ttl():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    with pytest.warns(DeprecationWarning):
        app._add_route(
            "/test/<string:user>/<name>", funct, methods=["GET"], cors=True, ttl=3600
        )
        funct_error = Mock(
            __name__="Mock", return_value=("NOK", "text/plain", "heyyyy")
        )
        app._add_route("/yo", funct_error, methods=["GET"], cors=True, ttl=3600)

    event = {
        "path": "/test/remote/pixel",
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
            "Cache-Control": "max-age=3600",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with(user="remote", name="pixel")

    event = {
        "path": "/yo",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    res = app(event, {})
    assert res["headers"]["Cache-Control"] == "no-cache"


def test_cache_control():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route(
        "/test/<string:user>/<name>",
        funct,
        methods=["GET"],
        cors=True,
        cache_control="public,max-age=3600",
    )
    funct_error = Mock(__name__="Mock", return_value=("NOK", "text/plain", "heyyyy"))
    app._add_route(
        "/yo",
        funct_error,
        methods=["GET"],
        cors=True,
        cache_control="public,max-age=3600",
    )

    event = {
        "path": "/test/remote/pixel",
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
            "Cache-Control": "public,max-age=3600",
        },
        "statusCode": 200,
    }
    res = app(event, {})
    assert res == resp
    funct.assert_called_with(user="remote", name="pixel")

    event = {
        "path": "/yo",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    res = app(event, {})
    assert res["headers"]["Cache-Control"] == "no-cache"


def test_querystringNull():
    """Add and parse route."""
    app = proxy.API(name="test")
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
    funct.assert_called_with(user="remotepixel")


def test_headersNull():
    """Add and parse route."""
    app = proxy.API(name="test")
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
    funct.assert_called_with(user="remotepixel")


def test_API_encoding():
    """Test b64 encoding."""
    app = proxy.API(name="test")

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

    app = proxy.API(name="test")
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

    app = proxy.API(name="test")
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
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<user>", funct, methods=["GET"], cors=True)

    event = {
        "route": "/users/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": '{"errorMessage": "Missing or invalid path"}',
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
        v="remotepixel",
        uuid="6b0d1f74-8f81-11e8-83fd-6a0003389b00",
        z=1,
        x=-1.0,
        ext="jpeg",
    )

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_routeToken(monkeypatch):
    """Validate tokens."""
    monkeypatch.setenv("TOKEN", "yo")

    app = proxy.API(name="test")
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
    funct.assert_called_with(user="remotepixel")

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
    funct.assert_called_with(user="remotepixel", inp=1)

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
    app = proxy.API(name="test")
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
    """Should work as expected on POST request."""
    app = proxy.API(name="test")
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
    funct.assert_called_with(user="remotepixel", body=b"0001")

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "POST",
        "headers": {},
        "queryStringParameters": {},
        "body": "eyJ5byI6ICJ5byJ9",
        "isBase64Encoded": True,
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
    funct.assert_called_with(user="remotepixel", body='{"yo": "yo"}')

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
    funct.assert_called_with(user="remotepixel")

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_ctx():
    """Should work as expected and pass ctx and evt to the function."""
    app = proxy.API(name="test")

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


def test_API_multipleRoute():
    """Should work as expected."""
    app = proxy.API(name="test")

    @app.route("/<user>", methods=["GET"], cors=True)
    @app.route("/<user>@<int:num>", methods=["GET"], cors=True)
    def print_id(user, num=None, params=None):
        return (
            "OK",
            "application/json",
            json.dumps({"user": user, "num": num, "params": params}),
        )

    event = {
        "path": "/remotepixel",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    res = app(event, {})
    body = json.loads(res["body"])
    assert res["statusCode"] == 200
    assert res["headers"] == headers
    assert body["user"] == "remotepixel"
    assert not body.get("num")
    assert not body.get("params")

    event = {
        "path": "/remotepixel@1",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {"params": "1"},
    }

    res = app(event, {})
    body = json.loads(res["body"])
    assert res["statusCode"] == 200
    assert res["headers"] == headers
    assert body["user"] == "remotepixel"
    assert body["num"] == 1
    assert body["params"] == "1"

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_doc():
    """Should work as expected."""
    app = proxy.API(name="test")

    @app.route("/test", methods=["POST"])
    def _post(body: str) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "Yo")

    @app.route("/<user>", methods=["GET"], tag=["users"], description="a route")
    def _user(user: str) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "Yo")

    @app.route("/<int:num>", methods=["GET"], token=True)
    def _num(num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<int:num>", methods=["GET"])
    def _userandnum(user: str, num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<float:num>", methods=["GET"])
    def _options(
        user: str,
        num: float = 1.0,
        opt1: str = "yep",
        opt2: int = 2,
        opt3: float = 2.0,
        **kwargs,
    ) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<num>", methods=["GET"])
    @app.pass_context
    @app.pass_event
    def _ctx(evt: Dict, ctx: Dict, user: str, num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    event = {
        "path": "/openapi.json",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    res = app(event, {})
    body = json.loads(res["body"])
    assert res["statusCode"] == 200
    assert res["headers"] == headers
    assert openapi_content == body

    event = {
        "path": "/docs",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "text/html",
    }

    res = app(event, {})
    assert res["statusCode"] == 200
    assert res["headers"] == headers

    event = {
        "path": "/redoc",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "text/html",
    }

    res = app(event, {})
    assert res["statusCode"] == 200
    assert res["headers"] == headers

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_doc_apigw():
    """Should work as expected if request from api-gateway."""
    app = proxy.API(name="test")

    @app.route("/test", methods=["POST"])
    def _post(body: str) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "Yo")

    @app.route("/<user>", methods=["GET"], tag=["users"], description="a route")
    def _user(user: str) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "Yo")

    @app.route("/<int:num>", methods=["GET"], token=True)
    def _num(num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<int:num>", methods=["GET"])
    def _userandnum(user: str, num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<float:num>", methods=["GET"])
    def _options(
        user: str,
        num: float = 1.0,
        opt1: str = "yep",
        opt2: int = 2,
        opt3: float = 2.0,
        **kwargs,
    ) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<num>", methods=["GET"])
    @app.pass_context
    @app.pass_event
    def _ctx(evt: Dict, ctx: Dict, user: str, num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    event = {
        "path": "/openapi.json",
        "httpMethod": "GET",
        "headers": {"Host": "afakeapi.execute-api.us-east-1.amazonaws.com"},
        "requestContext": {"stage": "production"},
        "queryStringParameters": {},
    }
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    res = app(event, {})
    body = json.loads(res["body"])
    assert res["statusCode"] == 200
    assert res["headers"] == headers
    assert openapi_apigw_content == body

    event = {
        "path": "/docs",
        "httpMethod": "GET",
        "headers": {"Host": "afakeapi.execute-api.us-east-1.amazonaws.com"},
        "requestContext": {"stage": "production"},
        "queryStringParameters": {},
    }
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "text/html",
    }

    res = app(event, {})
    assert res["statusCode"] == 200
    assert res["headers"] == headers

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_API_docCustomDomain():
    """Should work as expected."""
    app = proxy.API(name="test")

    @app.route("/test", methods=["POST"])
    def _post(body: str) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "Yo")

    @app.route("/<user>", methods=["GET"], tag=["users"], description="a route")
    def _user(user: str) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "Yo")

    @app.route("/<int:num>", methods=["GET"], token=True)
    def _num(num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<int:num>", methods=["GET"])
    def _userandnum(user: str, num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<float:num>", methods=["GET"])
    def _options(
        user: str,
        num: float = 1.0,
        opt1: str = "yep",
        opt2: int = 2,
        opt3: float = 2.0,
        **kwargs,
    ) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    @app.route("/<user>/<num>", methods=["GET"])
    @app.pass_context
    @app.pass_event
    def _ctx(evt: Dict, ctx: Dict, user: str, num: int) -> Tuple[str, str, str]:
        """Return something."""
        return ("OK", "text/plain", "yo")

    event = {
        "resource": "/{proxy+}",
        "pathParameters": {"proxy": "openapi.json"},
        "path": "/api/openapi.json",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    res = app(event, {})
    body = json.loads(res["body"])
    assert res["statusCode"] == 200
    assert res["headers"] == headers
    assert openapi_custom_content == body

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_routeRegex():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct_one = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    funct_two = Mock(__name__="Mock", return_value=("OK", "text/plain", "yooooo"))
    app._add_route(
        "/test/<regex([0-9]{4}):number>/<regex([a-z]{3}):name>",
        funct_two,
        methods=["GET"],
        cors=True,
    )
    app._add_route(
        "/test/<regex([0-9]{4}):number>/<name>", funct_one, methods=["GET"], cors=True
    )
    event = {
        "path": "/test/1234/pixel",
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
    funct_one.assert_called_with(number="1234", name="pixel")

    event = {
        "path": "/test/1234/pix",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    resp = {
        "body": "yooooo",
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
    funct_two.assert_called_with(number="1234", name="pix")

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def test_routeRegexFailing():
    """Add and parse route."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "yooooo"))
    app._add_route(
        r"/test/<regex(user(\d+)?):user>/<sport>", funct, methods=["GET"], cors=True
    )
    event = {
        "path": "/test/user1234/rugby",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }
    with pytest.raises(Exception):
        app(event, {})
        funct.assert_not_called()

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)


def testApigwPath():
    """test api call parsing."""
    # resource "/", no apigwg, noproxy, no path mapping
    event = {"path": "/test/1234/pix", "headers": {}}
    p = proxy.ApigwPath(event)
    assert p.path == "/test/1234/pix"
    assert not p.apigw_stage
    assert not p.api_prefix
    assert not p.path_mapping
    assert p.prefix == ""

    event = {"resource": "/", "path": "/test/1234/pix", "headers": {}}
    p = proxy.ApigwPath(event)
    assert p.path == "/test/1234/pix"
    assert not p.apigw_stage
    assert not p.api_prefix
    assert not p.path_mapping
    assert p.prefix == ""

    # resource "proxy+", no apigwg, no path mapping, no api prefix
    event = {
        "resource": "/{proxy+}",
        "pathParameters": {"proxy": "test/1234/pix"},
        "path": "/test/1234/pix",
        "headers": {},
    }
    p = proxy.ApigwPath(event)
    assert p.path == "/test/1234/pix"
    assert not p.apigw_stage
    assert not p.api_prefix
    assert not p.path_mapping
    assert p.prefix == ""

    # resource "proxy+", no apigwg, no path mapping, api prefix (api)
    event = {
        "resource": "/api/{proxy+}",
        "pathParameters": {"proxy": "test/1234/pix"},
        "path": "/api/test/1234/pix",
        "headers": {},
    }
    p = proxy.ApigwPath(event)
    assert p.path == "/test/1234/pix"
    assert not p.apigw_stage
    assert p.api_prefix == "/api"
    assert not p.path_mapping
    assert p.prefix == "/api"

    # resource "proxy+", no apigwg, path mapping (prefix), api prefix (api)
    event = {
        "resource": "/api/{proxy+}",
        "pathParameters": {"proxy": "test/1234/pix"},
        "path": "/prefix/api/test/1234/pix",
        "headers": {},
    }
    p = proxy.ApigwPath(event)
    assert p.path == "/test/1234/pix"
    assert not p.apigw_stage
    assert p.api_prefix == "/api"
    assert p.path_mapping == "/prefix"
    assert p.prefix == "/prefix/api"

    # resource "proxy+", apigwg (production), api prefix (api)
    event = {
        "resource": "/api/{proxy+}",
        "pathParameters": {"proxy": "test/1234/pix"},
        "path": "/prefix/api/test/1234/pix",
        "headers": {"host": "afakeapi.execute-api.us-east-1.amazonaws.com"},
        "requestContext": {"stage": "production"},
    }
    p = proxy.ApigwPath(event)
    assert p.path == "/test/1234/pix"
    assert p.apigw_stage == "/production"
    assert p.api_prefix == "/api"
    assert not p.path_mapping
    assert p.prefix == "/production/api"

    # resource "proxy+", apigwg ($default), api prefix (api)
    # $default is the default stage used with API Gateway's HTTP API
    # Should point to base URL
    event = {
        "resource": "/api/{proxy+}",
        "pathParameters": {"proxy": "test/1234/pix"},
        "path": "/prefix/api/test/1234/pix",
        "headers": {"host": "afakeapi.execute-api.us-east-1.amazonaws.com"},
        "requestContext": {"stage": "$default"},
    }
    p = proxy.ApigwPath(event)
    assert p.path == "/test/1234/pix"
    assert p.apigw_stage == "/$default"
    assert p.api_prefix == "/api"
    assert not p.path_mapping
    assert p.prefix == "/api"


def testApigwHostUrl():
    """Test url property."""
    app = proxy.API(name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<string:user>/<name>", funct, methods=["GET"], cors=True)

    # resource "/", no apigwg, noproxy, no path mapping
    event = {
        "path": "/test/1234/pix",
        "headers": {"Host": "test.apigw.com"},
        "httpMethod": "GET",
    }
    _ = app(event, {})
    assert app.host == "https://test.apigw.com"

    event = {
        "resource": "/",
        "path": "/test/1234/pix",
        "headers": {"Host": "test.apigw.com"},
        "httpMethod": "GET",
    }
    _ = app(event, {})
    assert app.host == "https://test.apigw.com"

    # resource "proxy+", apigwg (production), api prefix (api)
    event = {
        "resource": "/api/{proxy+}",
        "pathParameters": {"proxy": "test/1234/pix"},
        "path": "/api/test/1234/pix",
        "headers": {
            "X-Forwarded-Host": "abcdefghij.execute-api.eu-central-1.amazonaws.com"
        },
        "requestContext": {"stage": "production"},
        "httpMethod": "GET",
    }
    _ = app(event, {})
    assert (
        app.host
        == "https://abcdefghij.execute-api.eu-central-1.amazonaws.com/production"
    )

    # resource "proxy+", no apigwg, no path mapping, no api prefix
    event = {
        "resource": "/{proxy+}",
        "pathParameters": {"proxy": "test/1234/pix"},
        "path": "/test/1234/pix",
        "headers": {"Host": "test.apigw.com"},
        "httpMethod": "GET",
    }
    _ = app(event, {})
    assert app.host == "https://test.apigw.com"

    # resource "proxy+", no apigwg, path mapping (prefix), api prefix (api)
    event = {
        "resource": "/api/{proxy+}",
        "pathParameters": {"proxy": "test/1234/pix"},
        "path": "/prefix/api/test/1234/pix",
        "headers": {"Host": "test.apigw.com"},
        "httpMethod": "GET",
    }

    _ = app(event, {})
    assert app.host == "https://test.apigw.com/prefix"

    # Local
    app.https = False
    event = {
        "resource": "/",
        "path": "/api/test/1234/pix",
        "headers": {"Host": "127.0.0.0:8000"},
        "httpMethod": "GET",
    }

    _ = app(event, {})
    assert app.host == "http://127.0.0.0:8000"

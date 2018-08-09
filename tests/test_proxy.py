
import pytest
from mock import Mock

from lambda_proxy.proxy import Request, RouteEntry, API


funct = Mock(__name__="Mock")


def test_Request_valid():
    """Should work as expected."""
    event = {
        "queryStringParameters": {"user": "remotepixel"},
        "httpMethod": "GET",
        "path": "/test"
    }
    req = Request(event)
    assert req.query_params == {"user": "remotepixel"}
    assert req.url == "/test"
    assert req.method == "GET"


def tes2t_RouteEntry_init():
    """Should work as expected."""
    route = RouteEntry(funct, "my-function", "/endpoint/test/<id>", ["GET"], True, True)
    assert route.view_function == funct
    assert route.view_name == "my-function"
    assert route.methods == ["GET"]
    assert route.view_args == []
    assert route.cors
    assert route.token


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
    """Add  and parse route."""
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
        "path": "/test/remotepixel", "httpMethod": "GET", "queryStringParameters": {}
    }
    resp = {
        "body": "heyyyy",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": "200",
    }
    res = app(event, {})
    assert res == resp
    assert app.current_request.query_params == {}
    assert app.current_request.url == "/test/remotepixel"
    assert app.current_request.method == "GET"
    funct.assert_called_with("remotepixel")

    funct = Mock(
        __name__="Mock", return_value=("OK", "image/jpeg", "thisisafakeencodedjpeg")
    )
    app._add_route("/test/<user>.jpg", funct, methods=["GET"], cors=True)

    event = {
        "path": "/test/remotepixel.jpg",
        "httpMethod": "GET",
        "queryStringParameters": {},
    }
    resp = {
        "body": "thisisafakeencodedjpeg",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "image/jpeg",
        },
        "isBase64Encoded": True,
        "statusCode": "200",
    }
    res = app(event, {})
    assert res == resp


def test_API_routeURL():
    """Should catch invalid route and parse valid args."""
    app = API(app_name="test")
    funct = Mock(__name__="Mock", return_value=("OK", "text/plain", "heyyyy"))
    app._add_route("/test/<user>", funct, methods=["GET"], cors=True)

    event = {
        "route": "/users/remotepixel", "httpMethod": "GET", "queryStringParameters": {}
    }
    resp = {
        "body": '{"errorMessage": "Missing route parameter"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": "400",
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/users/remotepixel", "httpMethod": "GET", "queryStringParameters": {}
    }
    resp = {
        "body": '{"errorMessage": "No view function for: /users/remotepixel"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": "400",
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/test/remotepixel", "httpMethod": "POST", "queryStringParameters": {}
    }
    resp = {
        "body": '{"errorMessage": "Unsupported method: POST"}',
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "statusCode": "400",
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/users/remotepixel", "httpMethod": "GET", "queryStringParameters": {}
    }
    resp = {
        "body": '{"errorMessage": "No view function for: /users/remotepixel"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": "400",
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/test/users/remotepixel",
        "httpMethod": "GET",
        "queryStringParameters": {},
    }
    resp = {
        "body": '{"errorMessage": "No view function for: /test/users/remotepixel"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": "400",
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
        "statusCode": "200",
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
        "statusCode": "200",
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "queryStringParameters": {"access_token": "yep"},
    }
    resp = {
        "body": '{"message": "Invalid access token"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": "500",
    }
    res = app(event, {})
    assert res == resp

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "queryStringParameters": {"token": "yo"},
    }
    resp = {
        "body": '{"message": "Invalid access token"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": "500",
    }
    res = app(event, {})
    assert res == resp

    monkeypatch.delenv("TOKEN", raising=False)

    event = {
        "path": "/test/remotepixel",
        "httpMethod": "GET",
        "queryStringParameters": {"access_token": "yo"},
    }
    resp = {
        "body": '{"message": "Invalid access token"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": "500",
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
        "path": "/test/remotepixel", "httpMethod": "GET", "queryStringParameters": {}
    }
    resp = {
        "body": '{"errorMessage": "hey something went wrong"}',
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "statusCode": "500",
    }
    res = app(event, {})
    assert res == resp

    # Clear logger handlers
    for h in app.log.handlers:
        app.log.removeHandler(h)

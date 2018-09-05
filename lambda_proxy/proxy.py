"""Translate request from AWS api-gateway.

Freely adapted from https://github.com/aws/chalice

"""

import os
import re
import sys
import json
import logging

_PARAMS = re.compile(r"<[a-zA-Z0-9_]+\:?[a-zA-Z0-9_]+>")


class Request(object):
    """The current request from API gateway."""

    def __init__(self, event):
        """Initialize request object."""
        self.query_params = event["queryStringParameters"]
        self.method = event["httpMethod"]
        self.url = event["path"]


class RouteEntry(object):
    """Decode request path."""

    def __init__(
        self, view_function, view_name, path, methods, cors=False, token=False
    ):
        """Initialize route object."""
        self.view_function = view_function
        self.view_name = view_name
        self.uri_pattern = path
        self.methods = methods
        self.view_args = self._parse_view_args()
        self.cors = cors
        self.token = token

    def _parse_view_args(self):
        if "{" not in self.uri_pattern:
            return []

        # The [1:-1] slice is to remove the braces
        # e.g {foobar} -> foobar
        results = [r[1:-1] for r in _PARAMS.findall(self.uri_pattern)]
        return results

    def __eq__(self, other):
        """Check for equality."""
        return self.__dict__ == other.__dict__


class API(object):
    """API."""

    FORMAT_STRING = "[%(name)s] - [%(levelname)s] - %(message)s"

    def __init__(self, app_name, configure_logs=True, debug=False):
        """Initialize API object."""
        self.app_name = app_name
        self.routes = {}
        self.current_request = None
        self.debug = debug
        self.log = logging.getLogger(self.app_name)
        if configure_logs:
            self._configure_logging()

    def _configure_logging(self):
        if self._already_configured(self.log):
            return

        handler = logging.StreamHandler(sys.stdout)
        # Timestamp is handled by lambda itself so the
        # default FORMAT_STRING doesn't need to include it.
        formatter = logging.Formatter(self.FORMAT_STRING)
        handler.setFormatter(formatter)
        self.log.propagate = False
        if self.debug:
            level = logging.DEBUG
        else:
            level = logging.ERROR
        self.log.setLevel(level)
        self.log.addHandler(handler)

    def _already_configured(self, log):
        if not log.handlers:
            return False

        for handler in log.handlers:
            if isinstance(handler, logging.StreamHandler):
                if handler.stream == sys.stdout:
                    return True

        return False

    def _add_route(self, path, view_func, **kwargs):
        name = kwargs.pop("name", view_func.__name__)
        methods = kwargs.pop("methods", ["GET"])
        cors = kwargs.pop("cors", False)
        token = kwargs.pop("token", False)

        if kwargs:
            raise TypeError(
                "route() got unexpected keyword "
                "arguments: {}".format(", ".join(list(kwargs)))
            )

        if path in self.routes:
            raise ValueError(
                'Duplicate route detected: "{}"\n'
                "URL paths must be unique.".format(path)
            )

        entry = RouteEntry(view_func, name, path, methods, cors, token)
        self.routes[path] = entry

    def _url_convert(self, path):
        path = "^{}$".format(path)  # full match
        path = re.sub(r"<[a-zA-Z0-9_]+>", r"([a-zA-Z0-9_]+)", path)
        path = re.sub(r"<string\:[a-zA-Z0-9_]+>", r"([a-zA-Z0-9_]+)", path)
        path = re.sub(r"<int\:[a-zA-Z0-9_]+>", r"([0-9]+)", path)
        path = re.sub(r"<float\:[a-zA-Z0-9_]+>", "([+-]?[0-9]+\.[0-9]+)", path)
        path = re.sub(
            r"<uuid\:[a-zA-Z0-9_]+>",
            "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            path,
        )
        return path

    def _url_matching(self, url):
        for path, function in self.routes.items():
            route_expr = self._url_convert(path)
            expr = re.compile(route_expr)
            if expr.match(url):
                return path

        return ""

    def _converters(self, value, pathArg):
        conv_expr = re.compile(r"<[a-zA-Z0-9_]+\:[a-zA-Z0-9_]+>")
        if conv_expr.match(pathArg):
            if pathArg.split(":")[0] == "<int":
                return int(eval(value))

            elif pathArg.split(":")[0] == "<float":
                return float(eval(value))

            elif pathArg.split(":")[0] == "<string":
                return value

            elif pathArg.split(":")[0] == "<uuid":
                return value

            else:
                return value

        else:
            return value

    def _get_matching_args(self, route, url):
        route_expr = re.compile(r"<[a-zA-Z0-9_]+\:?[a-zA-Z0-9_]+>")
        url_expr = re.compile(self._url_convert(route))

        route_args = route_expr.findall(route)
        url_args = url_expr.match(url).groups()

        args = [
            self._converters(u, route_args[id])
            for id, u in enumerate(url_args)
            if u != route_args[id]
        ]
        return args

    def _validate_token(self, params):
        token = params.get("access_token", None)
        env_token = os.environ.get("TOKEN", None)

        if not token or not env_token:
            return False

        if token == env_token:
            return True

        return False

    def route(self, path, **kwargs):
        """Register route."""
        def _register_view(view_func):
            self._add_route(path, view_func, **kwargs)
            return view_func

        return _register_view

    def response(
        self, status, content_type, response_body, cors=False, methods=["GET"]
    ):
        """Return HTTP response.

        including response code (status), headers and body

        """
        statusCode = {
            "OK": "200",
            "EMPTY": "204",
            "NOK": "400",
            "FOUND": "302",
            "NOT_FOUND": "404",
            "CONFLICT": "409",
            "ERROR": "500",
        }

        binary_types = [
            "application/octet-stream",
            "application/x-tar",
            "application/zip",
            "image/png",
            "image/jpeg",
            "image/tiff",
            "image/webp",
        ]

        messageData = {
            "statusCode": statusCode[status],
            "body": response_body,
            "headers": {"Content-Type": content_type},
        }

        if cors:
            messageData["headers"]["Access-Control-Allow-Origin"] = "*"
            messageData["headers"]["Access-Control-Allow-Methods"] = ",".join(methods)
            messageData["headers"]["Access-Control-Allow-Credentials"] = "true"

        if content_type in binary_types:
            messageData["isBase64Encoded"] = True

        return messageData

    def __call__(self, event, context):
        """Initialize route and handlers."""
        self.log.debug(json.dumps(event.get("headers", {})))
        self.log.debug(json.dumps(event.get("queryStringParameters", {})))
        self.log.debug(json.dumps(event.get("pathParameters", {})))

        resource_path = event.get("path", None)
        if resource_path is None:
            return self.response(
                "NOK",
                "application/json",
                json.dumps({"errorMessage": "Missing route parameter"}),
            )

        if not self._url_matching(resource_path):
            return self.response(
                "NOK",
                "application/json",
                json.dumps(
                    {"errorMessage": "No view function for: {}".format(resource_path)}
                ),
            )

        route_entry = self.routes[self._url_matching(resource_path)]
        if route_entry.token:
            params = event.get("queryStringParameters", {})
            if not self._validate_token(params):
                return self.response(
                    "ERROR",
                    "application/json",
                    json.dumps({"message": "Invalid access token"}),
                )

        http_method = event["httpMethod"]
        if http_method not in route_entry.methods:
            return self.response(
                "NOK",
                "application/json",
                json.dumps(
                    {"errorMessage": "Unsupported method: {}".format(http_method)}
                ),
            )

        function_args = self._get_matching_args(route_entry.uri_pattern, resource_path)
        function_kwargs = {}
        if http_method == "POST":
            function_kwargs.update(dict(body=event.get("body", None)))

        self.current_request = Request(event)

        try:
            response = route_entry.view_function(*function_args, **function_kwargs)
        except Exception as err:
            self.log.error(str(err))
            response = (
                "ERROR",
                "application/json",
                json.dumps({"errorMessage": str(err)}),
            )

        return self.response(
            response[0],
            response[1],
            response[2],
            cors=route_entry.cors,
            methods=route_entry.methods,
        )

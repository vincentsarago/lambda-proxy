"""Translate request from AWS api-gateway.

Freely adapted from https://github.com/aws/chalice

"""

import os
import re
import sys
import json
import zlib
import base64
import logging

param_pattern = re.compile(
    r"^<" r"(?P<type>[a-zA-Z0-9_]+\:)?" r"(?P<name>[a-zA-Z0-9_]+)" r">$"
)

params_expr = re.compile(r"<([a-zA-Z0-9_]+\:)?[a-zA-Z0-9_]+>")


class RouteEntry(object):
    """Decode request path."""

    def __init__(
        self,
        view_function,
        view_name,
        path,
        methods=["GET"],
        cors=False,
        token="",
        payload_compression_method="",
        binary_b64encode=False,
        ttl=None,
    ):
        """Initialize route object."""
        self.view_function = view_function
        self.view_name = view_name
        self.uri_pattern = path
        self.methods = methods
        self.cors = cors
        self.token = token
        self.compression = payload_compression_method
        self.b64encode = binary_b64encode
        self.ttl = ttl
        if self.compression and self.compression not in ["gzip", "zlib", "deflate"]:
            raise ValueError(
                f"'{payload_compression_method}' is not a supported compression"
            )

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
        self.context = {}
        self.event = {}
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
        token = kwargs.pop("token", "")
        payload_compression = kwargs.pop("payload_compression_method", "")
        binary_encode = kwargs.pop("binary_b64encode", False)
        ttl = kwargs.pop("ttl", None)

        if kwargs:
            raise TypeError(
                "TypeError: route() got unexpected keyword "
                "arguments: %s" % ", ".join(list(kwargs))
            )

        if path in self.routes:
            raise ValueError(
                'Duplicate route detected: "{}"\n'
                "URL paths must be unique.".format(path)
            )

        self.routes[path] = RouteEntry(
            view_func,
            name,
            path,
            methods,
            cors,
            token,
            payload_compression,
            binary_encode,
            ttl,
        )

    def _url_convert(self, path):
        path = "^{}$".format(path)  # full match
        path = re.sub(r"<[a-zA-Z0-9_]+>", r"([a-zA-Z0-9_]+)", path)
        path = re.sub(r"<string\:[a-zA-Z0-9_]+>", r"([a-zA-Z0-9_]+)", path)
        path = re.sub(r"<int\:[a-zA-Z0-9_]+>", r"([0-9]+)", path)
        path = re.sub(r"<float\:[a-zA-Z0-9_]+>", "([+-]?[0-9]+.[0-9]+)", path)
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
        match = param_pattern.match(pathArg)
        if match:
            arg_type = match.groupdict()["type"]
            if arg_type == "int:":
                return int(value)
            elif arg_type == "float:":
                return float(value)
            elif arg_type == "string:":
                return value
            elif arg_type == "uuid:":
                return value
            else:
                return value
        else:
            return value

    def _get_matching_args(self, route, url):
        url_expr = re.compile(self._url_convert(route))

        route_args = [i.group() for i in params_expr.finditer(route)]
        url_args = url_expr.match(url).groups()

        names = [param_pattern.match(arg).groupdict()["name"] for arg in route_args]

        args = [
            self._converters(u, route_args[id])
            for id, u in enumerate(url_args)
            if u != route_args[id]
        ]

        return dict(zip(names, args))

    def _validate_token(self, token=None):
        env_token = os.environ.get("TOKEN")

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

    def pass_context(self, f):
        """Pass context to the function."""

        def new_func(*args, **kwargs):
            return f(self.context, *args, **kwargs)

        return new_func

    def pass_event(self, f):
        """Pass event to the function."""

        def new_func(*args, **kwargs):
            return f(self.event, *args, **kwargs)

        return new_func

    def response(
        self,
        status,
        content_type,
        response_body,
        cors=False,
        accepted_methods=[],
        accepted_compression="",
        compression="",
        b64encode=False,
        ttl=None,
    ):
        """Return HTTP response.

        including response code (status), headers and body

        """
        statusCode = {
            "OK": 200,
            "EMPTY": 204,
            "NOK": 400,
            "FOUND": 302,
            "NOT_FOUND": 404,
            "CONFLICT": 409,
            "ERROR": 500,
        }

        binary_types = [
            "application/octet-stream",
            "application/x-protobuf",
            "application/x-tar",
            "application/zip",
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/tiff",
            "image/webp",
            "image/jp2",
        ]

        messageData = {
            "statusCode": statusCode[status],
            "headers": {"Content-Type": content_type},
        }

        if cors:
            messageData["headers"]["Access-Control-Allow-Origin"] = "*"
            messageData["headers"]["Access-Control-Allow-Methods"] = ",".join(
                accepted_methods
            )
            messageData["headers"]["Access-Control-Allow-Credentials"] = "true"

        if compression and compression in accepted_compression:
            messageData["headers"]["Content-Encoding"] = compression
            if isinstance(response_body, str):
                response_body = bytes(response_body, "utf-8")

            if compression == "gzip":
                gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
                response_body = (
                    gzip_compress.compress(response_body) + gzip_compress.flush()
                )
            elif compression == "zlib":
                zlib_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)
                response_body = (
                    zlib_compress.compress(response_body) + zlib_compress.flush()
                )
            elif compression == "deflate":
                deflate_compress = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
                response_body = (
                    deflate_compress.compress(response_body) + deflate_compress.flush()
                )
            else:
                return self.response(
                    "ERROR",
                    "application/json",
                    json.dumps(
                        {"errorMessage": f"Unsupported compression mode: {compression}"}
                    ),
                )

        if ttl:
            messageData["headers"]["Cache-Control"] = f"max-age={ttl}"

        if (
            content_type in binary_types or not isinstance(response_body, str)
        ) and b64encode:
            messageData["isBase64Encoded"] = True
            messageData["body"] = base64.b64encode(response_body).decode()
        else:
            messageData["body"] = response_body

        return messageData

    def __call__(self, event, context):
        """Initialize route and handlers."""
        self.log.debug(json.dumps(event.get("headers", {})))
        self.log.debug(json.dumps(event.get("queryStringParameters", {})))
        self.log.debug(json.dumps(event.get("pathParameters", {})))

        self.event = event
        self.context = context

        headers = event.get("headers", {}) or {}
        headers = dict((key.lower(), value) for key, value in headers.items())

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
        request_params = event.get("queryStringParameters", {}) or {}
        if route_entry.token:
            if not self._validate_token(request_params.get("access_token")):
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

        # remove access_token from kwargs
        request_params.pop("access_token", False)

        function_kwargs = self._get_matching_args(
            route_entry.uri_pattern, resource_path
        )
        function_kwargs.update(request_params.copy())
        if http_method == "POST":
            function_kwargs.update(dict(body=event.get("body")))

        try:
            response = route_entry.view_function(**function_kwargs)
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
            accepted_methods=route_entry.methods,
            accepted_compression=headers.get("accept-encoding", ""),
            compression=route_entry.compression,
            b64encode=route_entry.b64encode,
            ttl=route_entry.ttl,
        )

# lambda-proxy

[![Packaging status](https://badge.fury.io/py/lambda-proxy.svg)](https://badge.fury.io/py/lambda-proxy)
[![CircleCI](https://circleci.com/gh/vincentsarago/lambda-proxy.svg?style=svg)](https://circleci.com/gh/vincentsarago/lambda-proxy)
[![codecov](https://codecov.io/gh/vincentsarago/lambda-proxy/branch/master/graph/badge.svg)](https://codecov.io/gh/vincentsarago/lambda-proxy)

A zero-requirement proxy linking AWS API Gateway `{proxy+}` requests and AWS Lambda.

<img width="600" alt="" src="https://user-images.githubusercontent.com/10407788/58742966-6ff50480-83f7-11e9-81f7-3ba7aa2310bb.png">

## Install

```bash
$ pip install -U pip
$ pip install lambda-proxy
```

Or install from source:

```bash
$ git clone https://github.com/vincentsarag/lambda-proxy.git
$ cd lambda-proxy
$ pip install -U pip
$ pip install -e .
```

# Usage

With GET request

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/test/tests/<id>', methods=['GET'], cors=True)
def print_id(id):
    return ('OK', 'plain/text', id)
```

With POST request

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/test/tests/<id>', methods=['POST'], cors=True)
def print_id(id, body):
    return ('OK', 'plain/text', id)
```

## Binary body

Starting from version 5.0.0, lambda-proxy will decode base64 encoded body on POST message.

Pre 5.0.0
```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/test', methods=['POST']e)
def print_id(body):
    body = json.loads(base64.b64decode(body).decode())
```

Post 5.0.0
```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/test', methods=['POST']e)
def print_id(body):
    body = json.loads(body)
```

# Routes 

Route schema is simmilar to the one used in [Flask](http://flask.pocoo.org/docs/1.0/api/#url-route-registrations)

> Variable parts in the route can be specified with angular brackets `/user/<username>`. By default a variable part in the URL accepts any string without a slash however a different converter can be specified as well by using `<converter:name>`.

Converters:
- `int`: integer
- `string`: string
- `float`: float number
- `uuid`: UUID

example: 
- `/app/<user>/<id>` (`user` and `id` are variables)
- `/app/<string:value>/<float:num>` (`value` will be a string, while `num` will be a float)

## Regex
You can also add regex parameters descriptions using special converter `regex()`

example: 
```python
@APP.route("/app/<regex([a-z]+):regularuser>", methods=['GET'])
def print_user(regularuser):
    return ('OK', 'plain/text', f"regular {regularuser}")

@APP.route("/app/<regex([A-Z]+):capitaluser>", methods=['GET'])
def print_user(capitaluser):
    return ('OK', 'plain/text', f"CAPITAL {capitaluser}")
```

#### Warning

when using **regex()** you must use different variable names or the route might not show up in the documentation.

```python
@APP.route("/app/<regex([a-z]+):user>", methods=['GET'])
def print_user(user):
    return ('OK', 'plain/text', f"regular {user}")

@APP.route("/app/<regex([A-Z]+):user>", methods=['GET'])
def print_user(user):
    return ('OK', 'plain/text', f"CAPITAL {user}")
```
This app will work but the documentation will only show the second route because in `openapi.json`, route names will be `/app/{user}` for both routes.

# Route Options 

- **path**: the URL rule as string
- **methods**: list of HTTP methods allowed, default: ["GET"]
- **cors**: allow CORS, default: `False`
- **token**: set `access_token` validation 
- **payload_compression_method**: Enable and select an output body compression
- **binary_b64encode**: base64 encode the output body (API Gateway)
- **ttl**: Cache Control setting (Time to Live) **(Deprecated in 6.0.0)**
- **cache_control**: Cache Control setting
- **description**: route description (for documentation)
- **tag**: list of tags (for documentation)

## Cache Control
	
Add a Cache Control header with a Time to Live (TTL) in seconds.

```python
from lambda_proxy.proxy import API
APP = API(app_name="app")

@APP.route('/test/tests/<id>', methods=['GET'], cors=True, cache_control="public,max-age=3600")
def print_id(id):
   return ('OK', 'plain/text', id)
```

Note: If function returns other then "OK", Cache-Control will be set to `no-cache`

## Binary responses

When working with binary on API-Gateway we must return a base64 encoded string

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/test/tests/<filename>.jpg', methods=['GET'], cors=True, binary_b64encode=True)
def print_id(filename):
    with open(f"{filename}.jpg", "rb") as f:
        return ('OK', 'image/jpeg', f.read())
```

## Compression

Enable compression if "Accept-Encoding" if found in headers.

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route(
   '/test/tests/<filename>.jpg',
   methods=['GET'],
   cors=True,
   binary_b64encode=True,
   payload_compression_method="gzip"
)
def print_id(filename):
    with open(f"{filename}.jpg", "rb") as f:
       return ('OK', 'image/jpeg', f.read())
```

## Simple Auth token

Lambda-proxy provide a simple token validation system.

-  a "TOKEN" variable must be set in the environment
-  each request must provide a "access_token" params (e.g curl
   http://myurl/test/tests/myid?access_token=blabla)

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/test/tests/<id>', methods=['GET'], cors=True, token=True)
def print_id(id):
    return ('OK', 'plain/text', id)
```

## URL schema and request parameters

QueryString parameters are passed as function's options.

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/<id>', methods=['GET'], cors=True)
def print_id(id, name=None):
    return ('OK', 'plain/text', f"{id}{name}")
```

requests:

```bash
$ curl /000001
   0001

$ curl /000001?name=vincent
   0001vincent
```

## Multiple Routes

```python
from lambda_proxy.proxy import API
APP = API(name="app")

@APP.route('/<id>', methods=['GET'], cors=True)
@APP.route('/<id>/<int:number>', methods=['GET'], cors=True)
def print_id(id, number=None, name=None):
    return ('OK', 'plain/text', f"{id}-{name}-{number}")
```
requests:

```bash

$ curl /000001
   0001--

$ curl /000001?name=vincent
   0001-vincent-

$ curl /000001/1?name=vincent
   0001-vincent-1
```

# Advanced features

## Context and Event passing

Pass event and context to the handler function.

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route("/<id>", methods=["GET"], cors=True)
@APP.pass_event
@APP.pass_context
def print_id(ctx, evt, id):
    print(ctx)
    print(evt)
    return ('OK', 'plain/text', f"{id}")
```

# Automatic OpenAPI documentation

By default the APP (`lambda_proxy.proxy.API`) is provided with three (3) routes: 
- `/openapi.json`: print OpenAPI JSON definition 

- `/docs`: swagger html UI 
![swagger](https://user-images.githubusercontent.com/10407788/58707335-9cbb0480-8382-11e9-927f-8d992cf2531a.jpg)

- `/redoc`: Redoc html UI 
![redoc](https://user-images.githubusercontent.com/10407788/58707338-9dec3180-8382-11e9-8dec-18173e39258f.jpg)

**Function annotations**

To be able to render full and precise API documentation, lambda_proxy uses python type hint and annotations [link](https://www.python.org/dev/peps/pep-3107/).

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/test/<int:id>', methods=['GET'], cors=True)
def print_id(id: int, num: float = 0.2) -> Tuple(str, str, str):
    return ('OK', 'plain/text', id)
```

In the example above, our route `/test/<int:id>` define an input `id` to be a `INT`, while we also add this hint to the function `print_id` we also specify the type (and default) of the `num` option. 

# Custom Domain and path mapping

Since version 4.1.1, lambda-proxy support custom domain and path mapping (see https://github.com/vincentsarago/lambda-proxy/issues/16).

Note: When using path mapping other than `root` (`/`), `/` route won't be available.

```python
from lambda_proxy.proxy import API

api = API(name="api", debug=True)


# This route won't work when using path mapping
@api.route("/", methods=["GET"], cors=True)
# This route will work only if the path mapping is set to /api
@api.route("/api", methods=["GET"], cors=True)
def index():
    html = """<!DOCTYPE html>
    <html>
        <header><title>This is title</title></header>
        <body>
            Hello world
        </body>
    </html>"""
    return ("OK", "text/html", html)


@api.route("/yo", methods=["GET"], cors=True)
def yo():
    return ("OK", "text/plain", "YOOOOO")
```

# Plugin

- Add cache layer: https://github.com/vincentsarago/lambda-proxy-cache


# Examples

-  https://github.com/vincentsarago/lambda-proxy/tree/master/example
-  https://github.com/RemotePixel/remotepixel-tiler


# Contribution & Devellopement

Issues and pull requests are more than welcome.

**Dev install & Pull-Request**

```bash
$ git clone https://github.com/vincentsarago/lambda-proxy.git
$ cd lambda-proxy
$ pip install -e .[dev]
```

This repo is set to use pre-commit to run *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when committing new code.

```bash
$ pre-commit install
$ git add .
$ git commit -m'my change'
   black.........................Passed
   Flake8........................Passed
   Verifying PEP257 Compliance...Passed
$ git push origin
```

### License

See [LICENSE.txt](/LICENSE.txt>).

### Authors

See [AUTHORS.txt](/AUTHORS.txt>).

### Changes

See [CHANGES.txt](/CHANGES.txt>).

# lambda-proxy

[![Packaging status](https://badge.fury.io/py/lambda-proxy.svg)](https://badge.fury.io/py/lambda-proxy)
[![CircleCI](https://circleci.com/gh/vincentsarago/lambda-proxy.svg?style=svg)](https://circleci.com/gh/vincentsarago/lambda-proxy)
[![codecov](https://codecov.io/gh/vincentsarago/lambda-proxy/branch/master/graph/badge.svg)](https://codecov.io/gh/vincentsarago/lambda-proxy)

A zero-requirement proxy linking AWS API Gateway `{proxy+}` requests and AWS Lambda.

<img width="600" alt="Capture d’écran, le 2019-05-31 à 22 56 35" src="https://user-images.githubusercontent.com/10407788/58742966-6ff50480-83f7-11e9-81f7-3ba7aa2310bb.png">

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

# Route Options 

- **path**: the URL rule as string
- **methods**: list of HTTP methods allowed, default: ["GET"]
- **cors**: allow CORS, default: `False`
- **token**: set `access_token` validation 
- **payload_compression_method**: Enable and select an output body compression
- **binary_b64encode**: base64 encode the output body (API Gateway)
- **ttl**: Cache Control setting (Time to Live)
- **description**: route description (for documentation)
- **tag**: list of tags (for documentation)

## Cache Control
	
Add a Cache Control header with a Time to Live (TTL) in seconds.

```python
from lambda_proxy.proxy import API
APP = API(app_name="app")

@APP.route('/test/tests/<id>', methods=['GET'], cors=True, ttl=3600)
def print_id(id):
   return ('OK', 'plain/text', id)
```

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
Enable compression (happens only if "Accept-Encoding" if found in
headers)

```python
from lambda_proxy.proxy import API

APP = API(name="app")

@APP.route('/test/tests/<filename>.jpg', methods=['GET'], cors=True, binary_b64encode=True, payload_compression_method="gzip")
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


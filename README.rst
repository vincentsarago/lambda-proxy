============
lambda-proxy
============

.. image:: https://badge.fury.io/py/lambda-proxy.svg
    :target: https://badge.fury.io/py/lambda-proxy

.. image:: https://circleci.com/gh/vincentsarago/lambda-proxy.svg?style=svg
    :target: https://circleci.com/gh/vincentsarago/lambda-proxy

.. image:: https://codecov.io/gh/vincentsarago/lambda-proxy/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/vincentsarago/lambda-proxy

A simple AWS Lambda proxy to handle API Gateway request

Install
=======

.. code-block:: console

    $ pip install -U pip
    $ pip install lambda-proxy

Or install from source:

.. code-block:: console

    $ git clone https://github.com/vincentsarag/lambda-proxy.git
    $ cd lambda-proxy
    $ pip install -U pip
    $ pip install -e .

Usage
=====

With GET request

.. code-block:: python

  >>> from lambda_proxy.proxy import API
  >>> APP = API(app_name="app")

  >>> @APP.route('/test/tests/<id>', methods=['GET'], cors=True)
  >>> def print_id(id):
          return ('OK', 'plain/text', id))


With POST request

.. code-block:: python

  >>> from lambda_proxy.proxy import API
  >>> APP = API(app_name="app")

  >>> @APP.route('/test/tests/<id>', methods=['POST'], cors=True)
  >>> def print_id(id, body):
          return ('OK', 'plain/text', id))


Simple Auth token

Lambda-proxy provide a simple token validation system.

- a "TOKEN" variable must be set in the environment
- each request must provide a "access_token" params (e.g `curl http://myurl/test/tests/myid?access_token=blabla`)

.. code-block:: python

  >>> from lambda_proxy.proxy import API
  >>> APP = API(app_name="app")

  >>> @APP.route('/test/tests/<id>', methods=['GET'], cors=True, token=True)
  >>> def print_id(id):
          return ('OK', 'plain/text', id))

URL schema and request parameters

.. code-block:: python

  >>> from lambda_proxy.proxy import API
  >>> APP = API(app_name="app")

  >>> @APP.route('/test/tests/<id>', methods=['GET'], cors=True)
  >>> def print_id(id, name=None):
          return ('OK', 'plain/text', f"{id}{name}"))

requests:

.. code-block::

  >>> curl /test/tests/000001
  0001

  >>> curl /test/tests/000001?name=vincent
  0001vincent


License
-------

See `LICENSE.txt <LICENSE.txt>`__.

Authors
-------

See `AUTHORS.txt <AUTHORS.txt>`__.

Changes
-------

See `CHANGES.txt <CHANGES.txt>`__.

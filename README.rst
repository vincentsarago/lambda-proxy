============
lambda-proxy
============

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

.. code-block:: python

  >>> from lambda_proxy.proxy import API
  >>> APP = API(app_name="app")

  >>> @APP.route('/test/tests/<id>', methods=['GET'], cors=True)
  >>> def print_id(id):
          return ('OK', 'plain/text', id))


License
-------

See `LICENSE.txt <LICENSE.txt>`__.

Authors
-------

See `AUTHORS.txt <AUTHORS.txt>`__.

Changes
-------

See `CHANGES.txt <CHANGES.txt>`__.

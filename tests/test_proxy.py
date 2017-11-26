
import os
import pytest

from lambda_proxy.proxy import Request, RouteEntry, API


def test_Request_valid():
    """Should work as expected (init Request Object)
    """
    query_params = {}
    url_params = {}
    method = 'GET'
    assert Request(query_params, url_params, method)


def test_RouteEntry_init():
    """Should work as expected (init RouteEntry Object)
    """
    def funct():
        """"""
        pass

    assert RouteEntry(funct, 'funct', '/endpoint/test/<id>/', ['GET'], True, True)


def test_API_init():
    """Should work as expected (init API Object)
    """
    assert API(app_name='test')

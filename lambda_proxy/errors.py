"""
lambda-proxy Errors.

Original code from
    - https://github.com/encode/starlette/blob/master/starlette/exceptions.py
    - https://github.com/tiangolo/fastapi/blob/master/fastapi/exceptions.py
"""

import http


class HTTPException(Exception):
    """Base HTTP Execption for lambda-proxy."""

    def __init__(
        self, status_code: int, detail: str = None, headers: dict = None
    ) -> None:
        """Set Exception."""
        if detail is None:
            detail = http.HTTPStatus(status_code).phrase

        self.status_code = status_code
        self.detail = detail
        self.headers = headers

    def __repr__(self) -> str:
        """Exception repr."""
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"

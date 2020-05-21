"""
Common response models.

Freely adapted from https://github.com/encode/starlette/blob/master/starlette/responses.py
"""

from typing import Any, Dict
import json


class Response:
    """Response Base Class."""

    media_type = None
    charset = "utf-8"

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Dict[str, str] = {},
        media_type: str = None,
    ) -> None:
        """Initiate Response."""
        self.body = self.render(content)
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type

        self.init_headers(headers)

    def render(self, content: Any) -> bytes:
        """Encode content."""
        if content is None:
            return b""
        if isinstance(content, bytes):
            return content
        return content.encode(self.charset)

    def init_headers(self, headers: Dict[str, str] = {}) -> None:
        """Create headers."""
        self._headers = headers.copy()
        if self.body:
            self._headers.update({"content-length": str(len(self.body))})

        if self.media_type:
            self._headers.update({"Content-Type": self.media_type})

    @property
    def headers(self) -> Dict:
        """Return response headers."""
        return self._headers


class XMLResponse(Response):
    """XML Response."""

    media_type = "application/xml"


class HTMLResponse(Response):
    """HTML Response."""

    media_type = "text/html"


class JSONResponse(Response):
    """JSON Response."""

    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        """Dump dict to JSON string."""
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


class PlainTextResponse(Response):
    """Plain Text Response."""

    media_type = "text/plain"

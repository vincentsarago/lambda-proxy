"""Launch server"""

import click
from urllib.parse import urlparse, parse_qsl

from http.server import HTTPServer, BaseHTTPRequestHandler

from app import APP


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """Requests handler."""

    def do_GET(self):
        """Get requests."""
        q = urlparse(self.path)
        request = {
            "headers": dict(self.headers),
            "path": q.path,
            "queryStringParameters": dict(parse_qsl(q.query)),
            "httpMethod": self.command,
        }
        response = APP(request, None)

        self.send_response(int(response["statusCode"]))
        for r in response["headers"]:
            self.send_header(r, response["headers"][r])
        self.end_headers()

        if isinstance(response["body"], str):
            self.wfile.write(bytes(response["body"], "utf-8"))
        else:
            self.wfile.write(response["body"])


@click.command(short_help="Local Server")
@click.option("--port", type=int, default=8000, help="port")
def run(port):
    """Launch server"""
    server_address = ("", port)
    httpd = HTTPServer(server_address, HTTPRequestHandler)
    click.echo(f"Starting local server at http://127.0.0.1:{port}", err=True)
    httpd.serve_forever()


if __name__ == "__main__":
    run()

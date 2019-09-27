"""lambda-proxy: A simple AWS Lambda proxy to handle API Gateway request."""

import pkg_resources

version = pkg_resources.get_distribution(__package__).version

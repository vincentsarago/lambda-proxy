
import os

from setuptools import setup, find_packages

with open('lambda_proxy/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            break


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='lambda_proxy',
      version=version,
      description=u"Simple AWS Lambda proxy to handle API Gateway request",
      long_description=u"Simple AWS Lambda proxy to handle API Gateway request",
      classifiers=['Programming Language :: Python :: 3.6'],
      keywords='AWS-Lambda API-Gateway Request Proxy',
      author=u"Vincent Sarago",
      author_email='vincent@mapbox.com',
      url='https://github.com/vincentsarago/lambda_proxy',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[],
      extras_require={
          'test': ['pytest', 'pytest-cov', 'codecov'],
      })

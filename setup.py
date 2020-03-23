"""Setup lambda_proxy."""

from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()


# Runtime requirements.
inst_reqs = []

extra_reqs = {"test": ["pytest", "pytest-cov", "mock"]}


setup(
    name="lambda-proxy",
    version="5.1.0",
    description=u"Simple AWS Lambda proxy to handle API Gateway request",
    long_description=readme,
    long_description_content_type="text/markdown",
    python_requires=">=3",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="AWS-Lambda API-Gateway Request Proxy",
    author=u"Vincent Sarago",
    author_email="vincent.sarago@gmail.com",
    url="https://github.com/vincentsarago/lambda-proxy",
    license="BSD",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)

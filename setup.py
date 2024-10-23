from setuptools import setup, find_packages
from configwebui import (
    __version__,
    __author__,
    __email__,
    __license__,
    __url__,
    __description__,
    __dependencies__,
)

PACKAGE_NAME = "configwebui-lucien"

setup(
    name=PACKAGE_NAME,
    version=__version__,
    author=__author__,
    author_email=__email__,
    url=__url__,
    license=__license__,
    description=__description__,
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=__dependencies__,
)

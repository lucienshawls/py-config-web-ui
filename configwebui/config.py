import os

"""
This module contains configuration settings for the `configwebui` package.

The configuration settings in this file are used to customize the behavior of the application,
including settings for Flask and other components of the package.

The `AppConfig` class provides default configuration values for the application, which can be
overridden by environment variables or custom configurations.

"""


class AppConfig:
    """
    A class that defines default configuration settings for the `configwebui` package.

    This class includes configurations for the Flask application and other global settings
    used by the package.

    Attributes:
        DEBUG (bool): A flag to enable or disable debugging mode (default is False).
        JSON_AS_ASCII (bool): A flag to specify whether JSON should be encoded as ASCII (default is False).
        SECRET_KEY (str): A secret key used by Flask for cryptographic operations.
                          It is either retrieved from an environment variable or generated randomly if not provided.

    Notes:
        The `SECRET_KEY` is used for session management and encryption within the Flask app.
        The `DEBUG` and `JSON_AS_ASCII` flags control Flask's debug mode and JSON encoding behavior, respectively.
    """

    DEBUG = False
    JSON_AS_ASCII = False
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24).hex()

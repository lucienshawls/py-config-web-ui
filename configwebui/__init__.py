"""
configwebui - A simple web-based configuration editor
for Python applications.

This package provides tools for editing configuration files
(like json or yaml) in a user-friendly web interface.
"""

__version__ = "0.1.0"
__author__ = "Lucien Shaw"
__email__ = "myxlc55@outlook.com"
__license__ = "MIT"
__url__ = "https://github.com/lucienshawls/py-config-web-ui"
__description__ = "A simple web-based configuration editor for Python applications."
__dependencies__ = ["Flask", "jsonschema"]
__keywords__ = ["configuration", "editor", "web", "tool", "json", "yaml", "ui", "flask"]
__all__ = ["ConfigEditor", "ResultStatus"]


import os
import signal
import logging
import threading
import contextlib
import webbrowser
from flask import Flask
from collections.abc import Callable
from jsonschema import validate, ValidationError

DEBUG = True


class ResultStatus:

    def set_status(self, status: bool) -> None:
        self.status = bool(status)

    def get_status(self) -> bool:
        return self.status

    def add_message(self, message: str) -> None:
        self.messages.append(str(message))

    def get_messages(self) -> list:
        return self.messages

    def __init__(self, status: bool, message: list[str] | str = None) -> None:
        self.set_status(status)
        self.messages = []
        if message is None:
            return
        if isinstance(message, list):
            for m in message:
                self.add_message(str(m))
        elif isinstance(message, str):
            self.add_message(message)
        else:
            raise TypeError(
                f"message must be a string or a list of strings, not {type(message)}"
            )

    def __bool__(self) -> bool:
        return self.status

    def __repr__(self) -> str:
        if len(self.messages) == 0:
            return f"ResultStatus(status={self.status}, messages=[])"
        else:
            return f"ResultStatus(status={self.status}, messages=[\n\t{',\n\t'.join(self.messages)}\n])"

    def __str__(self) -> str:
        if len(self.messages) == 0:
            return f'Current status: {"Success" if self.status else "Fail"}, Messages: (No messages).\n'
        else:
            return f'Current status: {"Success" if self.status else "Fail"}, Messages:\n\t{"\n\t".join(self.messages)}\n'


class UserConfig:
    @staticmethod
    def isvalid(config: dict | list = None) -> ResultStatus:
        return ResultStatus(True)

    def check(
        self,
        config: dict | list,
        schema: dict,
        skip_extra_validations: bool = False,
    ) -> ResultStatus:
        result = ResultStatus(True)
        try:
            validate(instance=config, schema=schema)
        except ValidationError as e:
            result.set_status(False)
            result.add_message(f"Schema validation error: {e.message}")
            return result
        if skip_extra_validations:
            return result
        extra_validation_result = self.extra_validation_func(config)
        if isinstance(extra_validation_result, ResultStatus):
            return extra_validation_result
        else:
            result.set_status(bool(extra_validation_result))
            return result

    def set_config(
        self,
        config: dict | list = None,
        schema: dict = None,
        skip_extra_validations: bool = False,
    ) -> ResultStatus:
        if config is None:
            config = self.config
        if schema is None:
            schema = self.schema
        if not (isinstance(config, list) or isinstance(config, dict)):
            raise TypeError(
                f"config must be a dictionary or a list, not {type(config)}"
            )
        if not isinstance(schema, dict):
            raise TypeError(f"schema must be a dictionary, not {type(schema)}")
        result = self.check(
            config=config, schema=schema, skip_extra_validations=skip_extra_validations
        )
        if result.get_status():
            self.config = config
            self.schema = schema
            return ResultStatus(True)
        else:
            return result

    def get_schema(self) -> dict:
        return self.schema

    def get_config(self) -> dict | list:
        return self.config

    def get_friendly_name(self) -> str:
        return self.friendly_name

    def __init__(
        self,
        friendly_name: str = "User Config",
        extra_validation_func: Callable = isvalid,
    ) -> None:
        if not isinstance(friendly_name, str):
            raise TypeError(
                f"friendly_name must be a string, not {type(friendly_name)}"
            )
        self.friendly_name = friendly_name
        if not callable(extra_validation_func):
            raise TypeError(
                f"extra_validation_func must be a callable function, not {type(extra_validation_func)}"
            )
        self.extra_validation_func = extra_validation_func
        self.config: dict | list = {}
        self.schema = {}


class ConfigEditor:
    def __init__(self, app_name: str = "Config Editor") -> None:
        from . import app
        from .config import AppConfig

        self.config_store: dict[str, UserConfig] = {}

        flask_app = Flask(
            import_name=app_name,
            template_folder="templates",
            static_folder="static",
            root_path=os.path.dirname(os.path.abspath(__file__)),
        )
        flask_app.config.from_object(AppConfig)
        flask_app.config["app_name"] = app_name
        flask_app.config["ConfigEditor"] = self
        flask_app.register_blueprint(app.main)
        flask_app.debug = DEBUG

        self.app = flask_app

    def delete_user_config(self, user_config_name: str) -> None:
        if user_config_name in self.config_store:
            del self.config_store[user_config_name]
        else:
            raise KeyError(f"Config {user_config_name} not found")

    def set_user_config(
        self,
        user_config_name: str,
        user_config_friendly_name: str = "User Config",
        user_config: dict | list = None,
        user_config_schema: dict = None,
        extra_validation_func: Callable = UserConfig.isvalid,
        skip_extra_validations: bool = True,
    ) -> None:
        if not isinstance(user_config_name, str):
            raise TypeError(
                f"user_config_name must be a string, not {type(user_config_name)}"
            )
        current_user_config = UserConfig(
            friendly_name=user_config_friendly_name,
            extra_validation_func=extra_validation_func,
        )
        result = current_user_config.set_config(
            config=user_config,
            schema=user_config_schema,
            skip_extra_validations=skip_extra_validations,
        )
        if not result.get_status():
            raise ValueError(f"Invalid config. Details:\n{result}")

        self.config_store[user_config_name] = current_user_config

    def get_user_config_names(self) -> list[str]:
        return list(self.config_store.keys())

    def get_user_config(self, user_config_name: str) -> dict | list:
        if user_config_name in self.config_store:
            return self.config_store[user_config_name].get_config()
        else:
            raise KeyError(f"Config {user_config_name} not found")

    def stop(self) -> None:
        os.kill(os.getpid(), signal.SIGINT)

    def run(self, host="localhost", port=80) -> None:
        url = (
            f"http://"
            f'{host if host!="0.0.0.0" and host!="[::]" else "localhost"}'
            f'{f":{port}" if port!=80 else ""}/'
        )
        print(f"Config Editor URL: {url}")
        print("Open the above link in your browser if it does not pop up.")
        print("\nPress Ctrl+C to stop.")
        if not DEBUG:
            threading.Timer(1, lambda: webbrowser.open(url)).start()
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            logging.getLogger("werkzeug").disabled = True
            self.app.run(host=host, port=port, use_reloader=DEBUG)
        self.stop()

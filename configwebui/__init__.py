"""
configwebui - A simple web-based configuration editor
for Python applications.

This package provides tools for editing configuration files
(like json or yaml) in a user-friendly web interface.
"""

__version__ = "0.2.0"
__author__ = "Lucien Shaw"
__email__ = "myxlc55@outlook.com"
__license__ = "MIT"
__url__ = "https://github.com/lucienshawls/py-config-web-ui"
__description__ = "A simple web-based configuration editor for Python applications."
__dependencies__ = ["Flask", "jsonschema"]
__keywords__ = ["configuration", "editor", "web", "tool", "json", "yaml", "ui", "flask"]
__all__ = ["ConfigEditor", "UserConfig", "ResultStatus"]


import os
import time
import logging
import threading
import webbrowser
from flask import Flask
from copy import deepcopy
from collections.abc import Callable
from socket import setdefaulttimeout
from werkzeug.serving import make_server
from jsonschema import validate, ValidationError

SERVER_TIMEOUT = 3
DAEMON_CHECK_INTERVAL = 1
logging.getLogger("werkzeug").disabled = True


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
            formatted_messages = ",\n\t".join(self.messages)
            return f"ResultStatus(status={self.status}, messages=[\n\t{formatted_messages}\n])"

    def __str__(self) -> str:
        if len(self.messages) == 0:
            return f'Current status: {"Success" if self.status else "Fail"}, Messages: (No messages).\n'
        else:
            formatted_messages = ",\n\t".join(self.messages)
            return f'Current status: {"Success" if self.status else "Fail"}, Messages:\n\t{formatted_messages}\n'


class UserConfig:
    DEFAULT_VALUE = {
        "string": "",
        "number": 0,
        "integer": 0,
        "boolean": False,
        "null": None,
    }

    @staticmethod
    def default_extra_validation_func(config: dict | list = None) -> ResultStatus:
        return ResultStatus(True)

    @staticmethod
    def default_save_func(config: dict | list) -> ResultStatus:
        return ResultStatus(False, "Save function is undefined")

    @staticmethod
    def add_order(schema: dict, property_order: int = 0) -> dict:
        ordered_schema = deepcopy(schema)
        ordered_schema["propertyOrder"] = property_order
        current_type = schema.get("type", None)
        if current_type == "object":
            for order, property in enumerate(ordered_schema.get("properties", {})):
                if "." in property:
                    raise ValueError(f"Property name cannot contain '.'")
                ordered_schema["properties"][property] = UserConfig.add_order(
                    schema=schema["properties"][property], property_order=order
                )
        elif current_type == "array":
            ordered_schema["items"] = UserConfig.add_order(
                schema=schema.get("items", {}), property_order=0
            )
        return ordered_schema

    @staticmethod
    def generate_default_json(schema: dict):
        if "default" in schema:
            return schema["default"]
        if "enum" in schema:
            return schema["enum"][0]
        current_type = schema.get("type", None)
        if current_type is None:
            return {}
        if schema["type"] == "object":
            obj = {}
            properties: dict = schema.get("properties", {})
            required: list = schema.get("required", [])
            for key, value in properties.items():
                if key in required:
                    obj[key] = UserConfig.generate_default_json(value)
            return obj
        elif schema["type"] == "array":
            min_items = schema.get("minItems", 0)
            return [
                UserConfig.generate_default_json(schema["items"])
                for _ in range(min_items)
            ]
        else:
            if isinstance(current_type, list):
                return UserConfig.DEFAULT_VALUE.get(current_type[0], None)
            else:
                return UserConfig.DEFAULT_VALUE.get(current_type, None)

    def check(
        self,
        config: dict | list,
        skip_schema_validations: bool = False,
        skip_extra_validations: bool = False,
    ) -> ResultStatus:
        result = ResultStatus(True)
        if not (isinstance(config, list) or isinstance(config, dict)):
            result.set_status(False)
            result.add_message(
                f"config must be a dictionary or a list, not {type(config)}"
            )
            return result
        if not skip_schema_validations:
            try:
                validate(instance=config, schema=self.schema)
            except ValidationError as e:
                result.set_status(False)
                result.add_message(f"Schema validation error: {e.message}")
                return result
        if not skip_extra_validations:
            extra_validation_result = self.extra_validation_func(config)
            if isinstance(extra_validation_result, ResultStatus):
                return extra_validation_result
            else:
                if not bool(extra_validation_result):
                    result.set_status(False)
                    result.add_message("Extra validation failed")
                    return result
        return result

    def set_config(
        self,
        config: dict | list = None,
        skip_schema_validations: bool = False,
        skip_extra_validations: bool = False,
    ) -> ResultStatus:
        if config is None:
            config = UserConfig.generate_default_json(self.schema)
        if not (isinstance(config, list) or isinstance(config, dict)):
            raise TypeError(
                f"config must be a dictionary or a list, not {type(config)}"
            )
        result = self.check(
            config=config,
            skip_schema_validations=skip_schema_validations,
            skip_extra_validations=skip_extra_validations,
        )
        if result.get_status():
            self.config = config
            return ResultStatus(True)
        else:
            return result

    def save(self) -> None:
        threading.Thread(target=self.save_func, args=(self.config,)).start()

    def get_name(self) -> str:
        return self.name

    def get_friendly_name(self) -> str:
        return self.friendly_name

    def get_schema(self) -> dict:
        return self.schema

    def get_config(self) -> dict | list:
        return self.config

    def __init__(
        self,
        name: str = "user_config",
        friendly_name: str = "User Config",
        schema: dict = None,
        extra_validation_func: Callable = default_extra_validation_func,
        save_func: Callable = default_save_func,
    ) -> None:
        if not isinstance(name, str):
            raise TypeError(
                f"friendly_name must be a string, not {type(friendly_name)}"
            )
        self.name = name
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
        if not callable(save_func):
            raise TypeError(
                f"extra_validation_func must be a callable function, not {type(extra_validation_func)}"
            )
        self.save_func = save_func
        if schema is None:
            schema = {}
        if not isinstance(schema, dict):
            raise TypeError(f"schema must be a dictionary, not {type(schema)}")
        self.schema = UserConfig.add_order(schema)
        self.config = {}


class ConfigEditor:
    @staticmethod
    def default_main_entry() -> None:
        return ResultStatus(False, "Main entry is undefined")

    def __init__(
        self, app_name: str = "Config Editor", main_entry: Callable = default_main_entry
    ) -> None:
        from . import app
        from .config import AppConfig

        if not isinstance(app_name, str):
            raise TypeError(f"app_name must be a string, not {type(app_name)}")
        if not callable(main_entry):
            raise TypeError(
                f"main_entry must be a callable function, not {type(main_entry)}"
            )
        self.running = False
        self.main_entry = main_entry
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

        self.app = flask_app

    def delete_user_config(self, user_config_name: str) -> None:
        if user_config_name in self.config_store:
            del self.config_store[user_config_name]
        else:
            raise KeyError(f"Config {user_config_name} not found")

    def add_user_config(
        self,
        user_config: UserConfig,
        replace: bool = False,
    ) -> None:
        if not isinstance(user_config, UserConfig):
            raise TypeError(
                f"user_config must be a UserConfig object, not {type(user_config)}"
            )
        user_config_name = user_config.get_name()
        if user_config_name in self.config_store and not replace:
            raise KeyError(f"Config {user_config_name} already exists")
        self.config_store[user_config_name] = user_config

    def get_user_config_names(self) -> list[str]:
        return list(self.config_store.keys())

    def get_user_config(self, user_config_name: str) -> UserConfig:
        if user_config_name in self.config_store:
            return self.config_store[user_config_name]
        else:
            raise KeyError(f"Config {user_config_name} not found")

    def launch_main_entry(self) -> None:
        threading.Thread(target=self.main_entry).start()

    def stop_server(self) -> None:
        self.running = False

    def start_server(self) -> None:
        self.server.serve_forever()

    def run(self, host="localhost", port=80) -> None:
        url = (
            f"http://"
            f'{host if host!="0.0.0.0" and host!="[::]" else "localhost"}'
            f'{f":{port}" if port!=80 else ""}/'
        )
        print(f"Config Editor URL: {url}")
        print("Open the above link in your browser if it does not pop up.")
        print("\nPress Ctrl+C to stop.")
        if not self.app.config["DEBUG"]:
            threading.Timer(1, lambda: webbrowser.open(url)).start()
        setdefaulttimeout(SERVER_TIMEOUT)
        self.server = make_server(host, port, self.app)

        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()
        self.running = True
        while self.running:
            try:
                time.sleep(DAEMON_CHECK_INTERVAL)
            except KeyboardInterrupt:
                if self.running:
                    self.stop_server()
        print("Please wait for the server to stop...")
        self.server.shutdown()
        server_thread.join()
        print("Server stopped.")

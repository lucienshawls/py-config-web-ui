"""\
configwebui - A simple web-based configuration editor
for Python applications.

This package provides tools for editing configuration files
(like json or yaml) in a user-friendly web interface.
"""

__all__ = ["ConfigEditor", "UserConfig", "ResultStatus"]

import os
import sys
import time
import logging
import threading
import traceback
import webbrowser
from flask import Flask
from io import StringIO
from copy import deepcopy
from collections.abc import Callable
from socket import setdefaulttimeout
from werkzeug.serving import make_server
from jsonschema import validate, ValidationError
from .__metadata__ import *

SERVER_TIMEOUT = 3
DAEMON_CHECK_INTERVAL = 1
READ_STREAM_INTERVAL = 0.01
BASE_OUTPUT_STREAM = sys.stdout
BASE_ERROR_STREAM = sys.stderr
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

    def copy(self) -> "ResultStatus":
        res = ResultStatus(self.status)
        for message in self.messages:
            res.add_message(message)
        return res

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


class ThreadOutputStream:
    def __init__(self, base_stream: StringIO) -> None:
        self.base_stream = base_stream
        self.streams: dict[str, StringIO] = {}

    def add_stream(self, thread_id: int, stream: StringIO) -> None:
        self.streams[thread_id] = stream

    def write(self, message: str) -> None:
        key = threading.current_thread().name
        stream = self.streams.get(key, self.base_stream)
        stream.write(message)

    def flush(self) -> None:
        key = threading.current_thread().name
        stream = self.streams.get(key, self.base_stream)
        stream.flush()


class ProgramRunner:
    def __init__(
        self,
        function: Callable,
        hide_terminal_output: bool = False,
        hide_terminal_error: bool = False,
    ) -> None:
        if not callable(function):
            raise TypeError(
                f"function must be a callable function, not {type(function)}"
            )
        self.function = function

        self.warning_occurred = False
        self.running = False
        self.res = ResultStatus(True)
        self.hide_terminal_output = hide_terminal_output
        self.hide_terminal_error = hide_terminal_error

        self.lock = threading.Lock()

        self.output = ""
        self.recently_added_output = ""

        self.error = ""
        self.recently_added_error = ""

    def capture_output(self) -> None:
        pointer_out = 0
        pointer_err = 0
        while self.running:
            self.io_out.seek(pointer_out)
            new_out = self.io_out.read()
            pointer_out += len(new_out)
            self.io_out.seek(pointer_out)
            if not self.hide_terminal_output:
                print(new_out, end="", file=BASE_OUTPUT_STREAM)

            self.io_err.seek(pointer_err)
            new_err = self.io_err.read()
            pointer_err += len(new_err)
            self.io_err.seek(pointer_err)

            if not self.hide_terminal_error:
                print(new_err, end="", file=BASE_ERROR_STREAM)

            with self.lock:
                self.output += new_out
                self.recently_added_output += new_out

                self.error += new_err
                self.recently_added_error += new_err
                if new_err != "":
                    self.warning_occurred = True
            time.sleep(READ_STREAM_INTERVAL)

    def run_in_separate_context(self, *args, **kwargs) -> None:
        if isinstance(sys.stdout, ThreadOutputStream):
            sys.stdout.add_stream(threading.current_thread().name, self.io_out)
        if isinstance(sys.stderr, ThreadOutputStream):
            sys.stderr.add_stream(threading.current_thread().name, self.io_err)
        try:
            res: ResultStatus | bool = self.function(*args, **kwargs)
            self.running = False
            self.capture_thread.join()
            with self.lock:
                if isinstance(res, ResultStatus):
                    self.res = res.copy()
                    if len(self.res.get_messages()) == 0:
                        self.res.add_message("Success.")
                elif isinstance(res, bool):
                    if not res:
                        self.res.set_status(False)
                        self.res.add_message("Failed.")
                    else:
                        self.res.add_message("Success.")
                else:
                    self.res.add_message("Success.")

        except Exception as e:
            self.running = False
            self.capture_thread.join()
            with self.lock:
                self.res.set_status(False)
                self.res.add_message(
                    "".join(traceback.format_exception_only(type(e), e)).strip()
                )
                new_err = traceback.format_exc()
                self.error += new_err
                self.recently_added_error += new_err

                if not self.hide_terminal_error:
                    print(new_err, end="", file=BASE_ERROR_STREAM)

    def run(self, *args, **kwargs) -> None:
        if hasattr(self, "program_thread") and self.program_thread.is_alive():
            return ResultStatus(False, "Program is already running")
        self.output = ""
        self.recently_added_output = ""

        self.error = ""
        self.recently_added_error = ""

        self.io_out = StringIO()
        self.io_err = StringIO()

        self.running = True
        self.warning_occurred = False
        self.res = ResultStatus(True)
        self.program_thread = threading.Thread(
            target=self.run_in_separate_context, args=args, kwargs=kwargs
        )
        self.capture_thread = threading.Thread(target=self.capture_output)
        self.program_thread.start()
        self.capture_thread.start()
        return ResultStatus(True)

    def get_output(self, recent_only: bool = False) -> str:
        with self.lock:
            if bool(recent_only):
                output = self.recently_added_output
            else:
                output = self.output
            self.recently_added_output = ""
        return output

    def get_error(self, recent_only: bool = False) -> str:
        with self.lock:
            if bool(recent_only):
                error = self.recently_added_error
            else:
                error = self.error
            self.recently_added_error = ""
        return error

    def get_res(self) -> ResultStatus:
        with self.lock:
            return self.res

    def has_warning(self) -> bool:
        with self.lock:
            return self.warning_occurred

    def is_running(self) -> bool:
        with self.lock:
            return self.running

    def wait_for_join(self) -> None:
        if hasattr(self, "program_thread"):
            self.program_thread.join()
        if hasattr(self, "capture_thread"):
            self.capture_thread.join()


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

    def save(self) -> ResultStatus:
        return self.save_func_runner.run(self.config)

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
        self.save_func_runner = ProgramRunner(
            function=save_func,
            hide_terminal_output=True,
            hide_terminal_error=False,
        )
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
        self.main_entry_runner = ProgramRunner(
            function=main_entry,
            hide_terminal_output=False,
            hide_terminal_error=False,
        )
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

    def launch_main_entry(self) -> ResultStatus:
        return self.main_entry_runner.run()

    def stop_server(self) -> None:
        self.running = False

    def start_server(self) -> None:
        self.server.serve_forever()

    def clean_up(self) -> None:
        print("Please wait for the server to stop... ", end="", file=BASE_OUTPUT_STREAM)
        self.server.shutdown()
        self.server_thread.join()
        print("Server stopped.", file=BASE_OUTPUT_STREAM)

        sys.stdout = BASE_OUTPUT_STREAM
        sys.stderr = BASE_ERROR_STREAM
        print("STDOUT and STDERR has been restored.")
        print("Please wait for the remaining threads to stop...")
        for user_config_name in self.get_user_config_names():
            self.get_user_config(user_config_name).save_func_runner.wait_for_join()
        self.main_entry_runner.wait_for_join()
        print("All remaining threads stopped.")

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

        sys.stdout = ThreadOutputStream(base_stream=BASE_OUTPUT_STREAM)
        sys.stderr = ThreadOutputStream(base_stream=BASE_ERROR_STREAM)

        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()
        self.running = True
        while self.running:
            try:
                time.sleep(DAEMON_CHECK_INTERVAL)
            except KeyboardInterrupt:
                if self.running:
                    self.stop_server()
        self.clean_up()

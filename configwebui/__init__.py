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
from datetime import datetime
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
                f"message must be a string or a list of strings, not {type(message)}."
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
        self.streams_to_terminal: dict[str, bool] = {}
        self.streams_lock: dict[str, threading.Lock] = {}

        self.shared_streams: dict[str, StringIO] = {}
        self.shared_streams_lock: dict[str, threading.Lock] = {}

        self.lock = threading.Lock()

    def add_stream(
        self,
        thread_id: str,
        stream: StringIO,
        lock: threading.Lock = threading.Lock(),
        to_terminal: bool = False,
    ) -> None:
        self.streams[thread_id] = stream
        self.streams_to_terminal[thread_id] = to_terminal
        self.streams_lock[thread_id] = lock

    def add_shared_stream(
        self,
        thread_id: str,
        shared_stream: StringIO,
        shared_lock: threading.Lock = threading.Lock(),
    ) -> None:
        self.shared_streams[thread_id] = shared_stream
        self.shared_streams_lock[thread_id] = shared_lock

    def write(self, message: str) -> None:
        thread_id = threading.current_thread().name
        stream = self.streams.get(thread_id, self.base_stream)
        lock = self.streams_lock.get(thread_id, self.lock)
        with lock:
            stream.write(message)
        if self.streams_to_terminal.get(thread_id, False):
            with self.lock:
                self.base_stream.write(message)
        shared_stream = self.shared_streams.get(thread_id, None)
        shared_lock = self.shared_streams_lock.get(thread_id, None)
        if (shared_stream is not None) and (shared_lock is not None):
            with shared_lock:
                shared_stream.write(message)

    def flush(self) -> None:
        thread_id = threading.current_thread().name
        stream = self.streams.get(thread_id, self.base_stream)
        lock = self.streams_lock.get(thread_id, self.lock)
        with lock:
            stream.flush()
        if self.streams_to_terminal.get(thread_id, False):
            with self.lock:
                self.base_stream.flush()
        shared_stream = self.shared_streams.get(thread_id, None)
        shared_lock = self.shared_streams_lock.get(thread_id, None)
        if (shared_stream is not None) and (shared_lock is not None):
            with shared_lock:
                shared_stream.flush()


class ProgramRunner:
    def __init__(
        self,
        function: Callable,
        hide_terminal_output: bool = False,
        hide_terminal_error: bool = False,
    ) -> None:
        if not callable(function):
            raise TypeError(
                f"function must be a callable function, not {type(function)}."
            )
        self.function = function

        self.running = False
        self.warning_occurred = False
        self.res = ResultStatus(True)

        self.io_out = StringIO()
        self.io_err = StringIO()
        self.io_combined = StringIO()

        self.hide_terminal_output = hide_terminal_output
        self.hide_terminal_error = hide_terminal_error

        self.lock = threading.Lock()
        self.output_lock = threading.Lock()
        self.error_lock = threading.Lock()
        self.combined_output_lock = threading.Lock()

        self.clear()

    def capture_output(self) -> None:
        if not self.running:
            return None
        with self.output_lock:
            new_out = self.io_out.getvalue()
            if new_out != "":
                self.io_out.truncate(0)
                self.io_out.seek(0)
        with self.error_lock:
            new_err = self.io_err.getvalue()
            if new_err != "":
                self.io_err.truncate(0)
                self.io_err.seek(0)
        with self.combined_output_lock:
            new_combined = self.io_combined.getvalue()
            if new_combined != "":
                self.io_combined.truncate(0)
                self.io_combined.seek(0)

        with self.lock:
            self.output += new_out
            self.recently_added_output += new_out

            self.error += new_err
            self.recently_added_error += new_err

            self.combined_output += new_combined
            self.recently_added_combined_output += new_combined

            if new_err != "":
                self.warning_occurred = True

    def run_in_separate_context(self, *args, **kwargs) -> None:
        thread_id = threading.current_thread().name
        try:
            assert isinstance(
                sys.stdout, ThreadOutputStream
            ), "Failed to hijack stdout."
            assert isinstance(
                sys.stderr, ThreadOutputStream
            ), "Failed to hijack stderr."
            sys.stdout.add_stream(
                thread_id=thread_id,
                stream=self.io_out,
                lock=self.output_lock,
                to_terminal=not self.hide_terminal_output,
            )
            sys.stdout.add_shared_stream(
                thread_id=thread_id,
                shared_stream=self.io_combined,
                shared_lock=self.combined_output_lock,
            )
            sys.stderr.add_stream(
                thread_id=thread_id,
                stream=self.io_err,
                lock=self.error_lock,
                to_terminal=not self.hide_terminal_error,
            )
            sys.stderr.add_shared_stream(
                thread_id=thread_id,
                shared_stream=self.io_combined,
                shared_lock=self.combined_output_lock,
            )

            formatted_time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f">_ [{formatted_time_now}]")
            res: ResultStatus | bool = self.function(*args, **kwargs)
            sys.stdout.flush()
            sys.stderr.flush()
            self.capture_output()
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
            self.running = False

        except Exception as e:
            sys.stdout.flush()
            sys.stderr.flush()
            self.capture_output()
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
            self.running = False

    def run(self, *args, **kwargs) -> None:
        if hasattr(self, "program_thread") and self.program_thread.is_alive():
            return ResultStatus(False, "Program is already running.")
        # self.clear()

        self.running = True
        self.warning_occurred = False
        self.res = ResultStatus(True)
        self.program_thread = threading.Thread(
            target=self.run_in_separate_context, args=args, kwargs=kwargs
        )
        self.program_thread.start()
        return ResultStatus(True)

    def get_output(self, recent_only: bool = False) -> str:
        self.capture_output()
        with self.lock:
            if bool(recent_only):
                output = self.recently_added_output
            else:
                output = self.output
            self.recently_added_output = ""
        return output

    def get_error(self, recent_only: bool = False) -> str:
        self.capture_output()
        with self.lock:
            if bool(recent_only):
                error = self.recently_added_error
            else:
                error = self.error
            self.recently_added_error = ""
        return error

    def get_combined_output(self, recent_only: bool = False) -> str:
        self.capture_output()
        with self.lock:
            if bool(recent_only):
                combined_output = self.recently_added_combined_output
            else:
                combined_output = self.combined_output
            self.recently_added_combined_output = ""
        return combined_output

    def get_res(self) -> ResultStatus:
        with self.lock:
            return self.res

    def clear(self) -> None:
        if self.is_running():
            return None
        with self.lock:
            self.output = ""
            self.recently_added_output = ""

            self.error = ""
            self.recently_added_error = ""

            self.combined_output = ""
            self.recently_added_combined_output = ""

            self.res = ResultStatus(True)
            self.warning_occurred = False

    def has_warning(self) -> bool:
        with self.lock:
            return self.warning_occurred

    def is_running(self) -> bool:
        with self.lock:
            return self.running

    def wait_for_join(self) -> None:
        if hasattr(self, "program_thread"):
            self.program_thread.join()


class UserConfig:
    DEFAULT_PROFILE_NAME = "Default"
    DEFAULT_VALUE = {
        "string": "",
        "number": 0,
        "integer": 0,
        "boolean": False,
        "null": None,
    }

    @staticmethod
    def default_extra_validation_func(name: str, config: dict) -> ResultStatus:
        return ResultStatus(True)

    @staticmethod
    def default_save_func(name: str, config: dict) -> ResultStatus:
        return ResultStatus(False, "Save function is undefined.")

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
        elif current_type is None:
            array_indicators = ["oneOf", "anyOf", "allOf"]
            for array_indicator in array_indicators:
                if array_indicator in ordered_schema:
                    for index, item in enumerate(ordered_schema[array_indicator]):
                        ordered_schema[array_indicator][index] = UserConfig.add_order(
                            schema=item, property_order=0
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
        config: dict,
        skip_schema_validations: bool = False,
        skip_extra_validations: bool = False,
    ) -> ResultStatus:
        result = ResultStatus(True)
        if not isinstance(config, dict):
            result.set_status(False)
            result.add_message(
                f"TypeError: config must be a dictionary, not {type(config)}."
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
            try:
                extra_validation_result = self.extra_validation_func(self.name, config)
                if isinstance(extra_validation_result, ResultStatus):
                    return extra_validation_result
                else:
                    if not bool(extra_validation_result):
                        result.set_status(False)
                        result.add_message("Extra validation failed.")
                        return result
            except Exception as e:
                result.set_status(False)
                result.add_message("Extra validation failed.")
                result.add_message(
                    "".join(traceback.format_exception_only(type(e), e)).strip()
                )
                return result
        return result

    def has_profile(self, name: str) -> bool:
        return name in self.config

    def add_profile(
        self,
        name: str,
        config: dict = None,
        save_file: bool = False,
    ) -> ResultStatus:
        if not isinstance(name, str):
            return ResultStatus(
                False, f"Profile name must be a string, not {type(name)}."
            )
        name = name.strip()
        if name == "":
            return ResultStatus(False, "Profile name cannot be empty.")
        if self.has_profile(name=name):
            return ResultStatus(False, f"Profile {name} already exists.")
        return self.update_profile(
            name=name,
            config=config,
            skip_schema_validations=True,
            skip_extra_validations=True,
            save_file=save_file,
        )

    def delete_profile(self, name: str, save_file: bool = False) -> ResultStatus:
        if not self.has_profile(name=name):
            return ResultStatus(True, f"Delete incomplete: profile {name} not found.")
        del self.config[name]
        if save_file:
            res_delete = self.save(profile_name=name, config=None)
            if not res_delete:
                return res_delete
        return ResultStatus(True)

    def update_profile(
        self,
        name: str = None,
        config: dict = None,
        skip_schema_validations: bool = False,
        skip_extra_validations: bool = False,
        save_file: bool = False,
    ) -> ResultStatus:
        if name is None:
            name = UserConfig.DEFAULT_PROFILE_NAME
        name = name.strip()
        if name == "":
            return ResultStatus(False, "Profile name cannot be empty.")
        if config is None:
            config = UserConfig.generate_default_json(self.schema)
        res_check = self.check(
            config=config,
            skip_schema_validations=skip_schema_validations,
            skip_extra_validations=skip_extra_validations,
        )
        if not res_check.get_status():
            return res_check
        if save_file:
            res_save = self.save(profile_name=name, config=config)
            if not res_save.get_status():
                return res_save
        self.config[name] = config
        return ResultStatus(True)

    def rename_profile(
        self,
        old_name: str,
        new_name: str,
        save_file: bool = False,
    ) -> ResultStatus:
        if not isinstance(old_name, str):
            return ResultStatus(
                False, f"Old profile name must be a string, not {type(old_name)}."
            )
        if not isinstance(new_name, str):
            return ResultStatus(
                False, f"New profile name must be a string, not {type(new_name)}."
            )
        if not self.has_profile(name=old_name):
            return ResultStatus(False, f"Profile {old_name} not found.")
        if self.has_profile(name=new_name):
            return ResultStatus(False, f"Profile {new_name} already exists.")
        res_new = self.update_profile(
            name=new_name,
            config=self.get_config(profile_name=old_name),
            skip_schema_validations=True,
            skip_extra_validations=True,
            save_file=save_file,
        )
        if not res_new:
            return res_new
        res_old = self.delete_profile(name=old_name, save_file=save_file)
        if not res_old.get_status():
            result = ResultStatus(
                True,
                f"Renaming incomplete, profile {old_name} may still be in the file.",
            )
            for message in res_old.get_messages():
                result.add_message(message)
            return result
        return ResultStatus(True)

    def save(self, profile_name, config: dict | None) -> ResultStatus:
        if hasattr(self, "saving") and self.saving:
            message = "Last save process has not finished yet, please try again later."
            return ResultStatus(False, message)
        else:
            self.saving = True

        try:
            res = self.save_func(self.name, profile_name, config)
        except Exception as e:
            res = ResultStatus(False, str(e))
        self.saving = False
        if isinstance(res, ResultStatus):
            if not res.get_status() and len(res.get_messages()) == 0:
                return ResultStatus(False, "An error occurred during file processing.")
            return res
        elif isinstance(res, bool):
            if res:
                return ResultStatus(True)
            else:
                return ResultStatus(False, "An error occurred during file processing.")
        else:
            return ResultStatus(True)

    def get_profile_names(self) -> list[str]:
        return list(self.config.keys())

    def get_name(self) -> str:
        return self.name

    def get_friendly_name(self) -> str:
        return self.friendly_name

    def get_schema(self) -> dict:
        return self.schema

    def get_config(self, profile_name: str) -> dict | None:
        return self.config.get(profile_name, None)

    def set_schema(self, schema: dict) -> None:
        if schema is None:
            schema = {}
        if not isinstance(schema, dict):
            raise TypeError(f"schema must be a dictionary, not {type(schema)}.")
        self.schema = UserConfig.add_order(schema)

    def __init__(
        self,
        name: str = "user_config",
        friendly_name: str = "User Config",
        schema: dict = None,
        extra_validation_func: Callable = None,
        save_func: Callable = None,
    ) -> None:
        if not isinstance(name, str):
            raise TypeError(
                f"friendly_name must be a string, not {type(friendly_name)}."
            )
        name = name.strip()
        if name == "":
            raise ValueError("Config name cannot be empty.")
        self.name = name
        if not isinstance(friendly_name, str):
            raise TypeError(
                f"friendly_name must be a string, not {type(friendly_name)}."
            )
        friendly_name = friendly_name.strip()
        if friendly_name == "":
            raise ValueError("Config friendly name cannot be empty.")
        self.friendly_name = friendly_name

        if extra_validation_func is None:
            self.extra_validation_func = UserConfig.default_extra_validation_func
        else:
            if not callable(extra_validation_func):
                raise TypeError(
                    f"extra_validation_func must be a callable function, not {type(extra_validation_func)}."
                )
            self.extra_validation_func = extra_validation_func
        if save_func is None:
            self.save_func = UserConfig.default_save_func
        else:
            if not callable(save_func):
                raise TypeError(
                    f"save_func must be a callable function, not {type(extra_validation_func)}"
                )
            self.save_func = save_func
        self.set_schema(schema=schema)
        self.config = {}


class ConfigEditor:
    @staticmethod
    def default_main_entry() -> None:
        return ResultStatus(False, "Main entry is undefined.")

    def __init__(
        self,
        app_name: str = "Config Editor",
        main_entry: Callable = None,
    ) -> None:
        from . import app
        from .config import AppConfig

        if not isinstance(app_name, str):
            raise TypeError(f"app_name must be a string, not {type(app_name)}.")
        app_name = app_name.strip()
        if app_name == "":
            raise ValueError("app_name cannot be empty.")
        if main_entry is None:
            self.main_entry_runner = ProgramRunner(
                function=ConfigEditor.default_main_entry,
                hide_terminal_output=False,
                hide_terminal_error=False,
            )
        else:
            if not callable(main_entry):
                raise TypeError(
                    f"main_entry must be a callable function, not {type(main_entry)}."
                )
            self.main_entry_runner = ProgramRunner(
                function=main_entry,
                hide_terminal_output=False,
                hide_terminal_error=False,
            )

        self.app_name = app_name
        self.running = False
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
            raise KeyError(f"Config {user_config_name} not found.")

    def add_user_config(
        self,
        user_config: UserConfig,
        replace: bool = False,
    ) -> None:
        if not isinstance(user_config, UserConfig):
            raise TypeError(
                f"user_config must be a UserConfig object, not {type(user_config)}."
            )
        user_config_name = user_config.get_name()
        if user_config_name in self.config_store and not replace:
            raise KeyError(f"Config {user_config_name} already exists.")
        self.config_store[user_config_name] = user_config

    def get_user_config_names(self) -> list[str]:
        return list(self.config_store.keys())

    def get_user_config(self, user_config_name: str) -> UserConfig:
        if user_config_name in self.config_store:
            return self.config_store[user_config_name]
        else:
            raise KeyError(f"Config {user_config_name} not found.")

    def launch_main_entry(self) -> ResultStatus:
        return self.main_entry_runner.run()

    def stop_server(self) -> None:
        self.running = False

    def start_server(self) -> None:
        self.server.serve_forever()

    def clean_up(self) -> None:
        print("\nGracefully terminating...", file=BASE_OUTPUT_STREAM)
        print(f"Please wait for the server to stop...", end="", file=BASE_OUTPUT_STREAM)
        self.server.shutdown()
        self.server_thread.join()
        print(f'\rServer stopped.{" "*25}', file=BASE_OUTPUT_STREAM)

        print(f"Restoring stdout and stderr...", end="", file=BASE_OUTPUT_STREAM)
        sys.stdout = BASE_OUTPUT_STREAM
        sys.stderr = BASE_ERROR_STREAM
        print(f'\rRestored stdout and stderr.{" "*5}')
        print("Please wait for the remaining threads to stop...")
        self.main_entry_runner.wait_for_join()
        print("All remaining threads stopped.")

    def run(self, host="localhost", port=80) -> None:
        if len(self.get_user_config_names()) == 0:
            raise ValueError("No UserConfig object found. Please add at least one.")
        url = (
            f"http://"
            f'{host if host!="0.0.0.0" and host!="[::]" else "localhost"}'
            f'{f":{port}" if port!=80 else ""}/'
        )
        print(f"Config Editor ({self.app_name}) URL: {url}")
        print("Open the above link in your browser if it does not pop up.")
        print("\nPress Ctrl+C to stop.")
        threading.Thread(target=webbrowser.open, args=(url,)).start()
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

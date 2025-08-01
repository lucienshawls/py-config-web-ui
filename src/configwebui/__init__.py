"""
configwebui - A simple web-based configuration editor
for Python applications.

This package provides tools for editing configuration files
(like json or yaml) in a user-friendly web interface.

This module contains the core functionality of the `configwebui` package. It provides classes and methods
for building and managing a web-based configuration editor interface.

The primary components of this module include:

- `ConfigEditor`: The main class that manages the configuration editor, including handling user configurations,
  launching the web server, and providing a user-friendly interface for editing and validating configurations.

- `UserConfig`: A class that represents individual user configurations, enabling storage, validation, and
  management of user-provided configuration data.

- `ResultStatus`: A class representing the status of an operation (success/failure) with associated messages.

This module also manages the configuration flow, including:
- Adding, retrieving, and deleting user configurations.
- Running the main entry point function and capturing its output.
- Starting and stopping the web server that serves the configuration editor.
- Handling server cleanup and restoring the terminal output.

The `configwebui` package allows developers to quickly generate an interactive web-based UI for configuration editing,
making it easier for users to modify and validate configuration files visually without needing to interact with
configuration file syntax directly. It supports real-time validation and error reporting, asynchronous saving of
configuration data, and easy execution of programs with user-defined configurations.

Note:
    This module relies on several external libraries, including Flask for the web server, and `werkzeug` for
    handling requests. It also makes use of `threading` for managing concurrent operations like running the server
    and handling output streams.

Usage Example:
    ```python
    from configwebui import ConfigEditor, UserConfig

    # Define a UserConfig
    user_config = UserConfig(name="my_config", schema={...})

    # Initialize the ConfigEditor and add the configuration
    editor = ConfigEditor(app_name="My Config Editor")
    editor.add_user_config(user_config)

    # Run the configuration editor
    editor.run()
    ```

This module serves as the foundation for the `configwebui` package and enables developers to integrate
a customizable configuration interface into their applications with minimal effort.

"""

import logging
import os
import sys
import threading
import time
import traceback
import webbrowser
from collections.abc import Callable
from copy import deepcopy
from importlib.metadata import version, PackageNotFoundError
from socket import setdefaulttimeout

from flask import Flask
from jsonschema import ValidationError, validate
from werkzeug.serving import make_server

from .runner import (
    BASE_ERROR_STREAM,
    BASE_OUTPUT_STREAM,
    ProgramRunner,
    ResultStatus,
    ThreadOutputStream,
)
from .utils import ResultStatus

try:
    __version__ = version("configwebui-lucien")
except PackageNotFoundError:
    pass
__all__ = ["ConfigEditor", "UserConfig", "ResultStatus"]

SERVER_TIMEOUT = 3
DAEMON_CHECK_INTERVAL = 1
logging.getLogger("werkzeug").disabled = True


class UserConfig:
    """
    A class for managing user configuration profiles, including validation, schema handling,
    profile management (add, update, delete, rename), and saving configurations to a file.

    Attributes:
        DEFAULT_PROFILE_NAME (str): The default profile name to be used when no profile name is provided.
        DEFAULT_VALUE (dict): Default values for different data types (string, number, integer, boolean, null).
        name (str): The name of the configuration.
        friendly_name (str): A user-friendly name for the configuration.
        schema (dict): The schema used for validation and generation of configuration data.
        extra_validation_func (Callable): A callable function for additional custom validation on configuration.
        save_func (Callable): A callable function for saving the configuration.
        config (dict): A dictionary holding all configuration profiles.
        saving (bool): A flag indicating whether a save operation is currently in progress.

    Methods:
        default_extra_validation_func(name: str, config: dict) -> ResultStatus:
            A default function for additional validation of a configuration.

        default_save_func(name: str, config: dict) -> ResultStatus:
            A default save function when no custom save function is provided.

        add_order(schema: dict, property_order: int = 0) -> dict:
            Adds property order to a given schema, useful for ensuring properties are serialized in a consistent order.

        generate_default_json(schema: dict):
            Generates a default JSON configuration based on the provided schema.

        check(
            config: dict,
            skip_schema_validations: bool = False,
            skip_extra_validations: bool = False
        ) -> ResultStatus:
            Validates the provided configuration against the schema and custom validation functions.

        has_profile(name: str) -> bool:
            Checks if a configuration profile with the given name exists.

        add_profile(
            name: str,
            config: dict | None = None,
            save_file: bool = False
        ) -> ResultStatus:
            Adds a new profile with the provided name and configuration.

        delete_profile(name: str, save_file: bool = False) -> ResultStatus:
            Deletes the profile with the given name.

        update_profile(
            name: str | None = None,
            config: dict | None = None,
            skip_schema_validations: bool = False,
            skip_extra_validations: bool = False,
            save_file: bool = False
        ) -> ResultStatus:
            Updates an existing profile with the new configuration.

        rename_profile(
            old_name: str,
            new_name: str,
            save_file: bool = False
        ) -> ResultStatus:
            Renames an existing profile.

        save(profile_name, config: dict | None) -> ResultStatus:
            Saves the profile configuration to a file.

        get_profile_names() -> list[str]:
            Retrieves the list of all profile names.

        get_name() -> str:
            Returns the name of the configuration.

        get_friendly_name() -> str:
            Returns the user-friendly name of the configuration.

        get_schema() -> dict:
            Retrieves the schema associated with the configuration.

        get_config(profile_name: str) -> dict | None:
            Retrieves the configuration for a given profile name.

        set_schema(schema: dict) -> None:
            Sets or updates the schema for the configuration.

        __init__(
            self,
            name: str = "user_config",
            friendly_name: str = "User Config",
            schema: dict | None = None,
            extra_validation_func: Callable | None = None,
            save_func: Callable | None = None
        ) -> None:
            Initializes a new instance of UserConfig with the provided parameters.
    """

    DEFAULT_PROFILE_NAME = "Default"
    DEFAULT_VALUE = {
        "string": "",
        "number": 0,
        "integer": 0,
        "boolean": False,
        "null": None,
    }

    def __init__(
        self,
        name: str = "user_config",
        friendly_name: str = "User Config",
        schema: dict | None = None,
        extra_validation_func: Callable | None = None,
        save_func: Callable | None = None,
        default_profile_only: bool = False,
    ) -> None:
        """
        Initializes a UserConfig instance.

        Args:
            name (str): Unique name for the configuration instance. Default is 'user_config'.
            friendly_name (str): Human-friendly name for the configuration instance. Default is 'User Config'.
            schema (dict | None): JSON schema for validating configuration profiles. Default is None.
            extra_validation_func (Callable | None): Optional additional validation function for profiles.
            save_func (Callable | None): Optional save function for persisting profiles.

        Raises:
            TypeError: If `name`, `friendly_name`, or validation/save functions are not of expected types.
            ValueError: If `name` or `friendly_name` is an empty string.
        """
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

        if not isinstance(default_profile_only, bool):
            raise TypeError(
                f"default_profile_only must be a boolean, not {type(default_profile_only)}."
            )

        self.default_profile_only = default_profile_only

    @staticmethod
    def default_extra_validation_func(
        name: str,
        config: dict | None,
    ) -> ResultStatus:
        """
        Default extra validation function.

        Args:
            name (str): Configuration name.
            config (dict or None): Configuration data to validate.

        Returns:
            ResultStatus: Always returns a successful status.
        """
        return ResultStatus(True)

    @staticmethod
    def default_save_func(name: str, config: dict) -> ResultStatus:
        """
        Default save function.

        Args:
            name (str): Profile name.
            config (dict): Configuration data to save.

        Returns:
            ResultStatus: Returns a failure status indicating the function is undefined.
        """
        return ResultStatus(False, "Save function is undefined.")

    @staticmethod
    def add_order(schema: dict, property_order: int = 0) -> dict:
        """
        Adds a `propertyOrder` field to a JSON schema for UI ordering.

        Args:
            schema (dict): The JSON schema to modify.
            property_order (int): The order value to assign to the schema properties.

        Returns:
            dict: The schema with `propertyOrder` fields added.

        Raises:
            ValueError: If property names contain '.'.
        """
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
        """
        Generates a default JSON configuration based on a schema.

        Args:
            schema (dict): The JSON schema to use.

        Returns:
            Any: The default configuration data inferred from the schema.
        """
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
        """
        Validates a configuration against the schema and optional extra validation.

        Args:
            config (dict): The configuration data to validate.
            skip_schema_validations (bool): Whether to skip schema validation.
            skip_extra_validations (bool): Whether to skip extra validation.

        Returns:
            ResultStatus: Validation result.
        """
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
        """
        Checks if a profile exists.

        Args:
            name (str): Profile name.

        Returns:
            bool: True if the profile exists, False otherwise.
        """
        return name in self.config

    def add_profile(
        self,
        name: str,
        config: dict | None = None,
        save_file: bool = False,
    ) -> ResultStatus:
        """
        Adds a new profile.

        Args:
            name (str): Profile name.
            config (dict | None): Initial configuration data. Defaults to None.
            save_file (bool): Whether to save the profile to a file by calling
                save() method. Defaults to False.

        Returns:
            ResultStatus: Result of the operation.
        """
        if not isinstance(name, str):
            return ResultStatus(
                False, f"Profile name must be a string, not {type(name)}."
            )
        name = name.strip()
        if name == "":
            return ResultStatus(False, "Profile name cannot be empty.")
        if self.has_profile(name=name):
            return ResultStatus(False, f"Profile {name} already exists.")
        if name != UserConfig.DEFAULT_PROFILE_NAME and self.default_profile_only:
            return ResultStatus(
                False, "Custom profiles are disabled, use the default profile only."
            )
        return self.update_profile(
            name=name,
            config=config,
            skip_schema_validations=True,
            skip_extra_validations=True,
            save_file=save_file,
        )

    def delete_profile(self, name: str, save_file: bool = False) -> ResultStatus:
        """
        Deletes an existing profile.

        Args:
            name (str): Profile name.
            save_file (bool): Whether to delete the profile from a file. Defaults to False.

        Returns:
            ResultStatus: Result of the deletion.
        """
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
        name: str | None = None,
        config: dict | None = None,
        skip_schema_validations: bool = False,
        skip_extra_validations: bool = False,
        save_file: bool = False,
    ) -> ResultStatus:
        """
        Updates or creates a profile.

        Args:
            name (str | None): Profile name. Defaults to the default profile name.
            config (dict | None): Configuration data. Defaults to schema defaults.
            skip_schema_validations (bool): Whether to skip schema validation.
            skip_extra_validations (bool): Whether to skip extra validation.
            save_file (bool): Whether to save the profile to a file. Defaults to False.

        Returns:
            ResultStatus: Result of the operation.
        """
        if not isinstance(name, str) and name is not None:
            return ResultStatus(
                False, f"Profile name must be a string, not {type(name)}."
            )
        if name is None:
            name = UserConfig.DEFAULT_PROFILE_NAME
        name = name.strip()
        if name == "":
            return ResultStatus(False, "Profile name cannot be empty.")
        if self.default_profile_only and name != UserConfig.DEFAULT_PROFILE_NAME:
            return ResultStatus(
                False, "Custom profiles are disabled, use the default profile only."
            )
        if config is None:
            config = UserConfig.generate_default_json(self.schema)
        res_check = self.check(
            config=config,
            skip_schema_validations=skip_schema_validations,
            skip_extra_validations=skip_extra_validations,
        )
        if not res_check.get_status():
            return res_check
        self.config[name] = config
        if save_file:
            res_save = self.save(profile_name=name, config=config)
            if not res_save.get_status():
                del self.config[name]
                return res_save
        return ResultStatus(True)

    def rename_profile(
        self,
        old_name: str,
        new_name: str,
        save_file: bool = False,
    ) -> ResultStatus:
        """
        Renames an existing profile.

        Args:
            old_name (str): Current profile name.
            new_name (str): New profile name.
            save_file (bool): Whether to save the renamed profile. Defaults to False.

        Returns:
            ResultStatus: Result of the operation.
        """
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
        """
        Saves a profile to storage.

        Args:
            profile_name (str): Profile name.
            config (dict | None): Configuration data to save. Defaults to None.

        Returns:
            ResultStatus: Result of the save operation.
        """
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
        """
        Retrieves all profile names.

        Returns:
            list[str]: List of profile names.
        """
        return list(self.config.keys())

    def get_name(self) -> str:
        """
        Retrieves the configuration instance name.

        Returns:
            str: Configuration name.
        """
        return self.name

    def get_friendly_name(self) -> str:
        """
        Retrieves the friendly name of the configuration instance.

        Returns:
            str: Friendly name.
        """
        return self.friendly_name

    def get_schema(self) -> dict:
        """
        Retrieves the JSON schema.

        Returns:
            dict: JSON schema.
        """
        return deepcopy(self.schema)

    def get_config(self, profile_name: str) -> dict | None:
        """
        Retrieves the configuration of a specific profile.

        Args:
            profile_name (str): Profile name.

        Returns:
            dict | None: Configuration data or None if the profile does not exist.
        """
        return self.config.get(profile_name, None)

    def set_schema(self, schema: dict) -> None:
        """
        Sets a new JSON schema and updates its property order.

        Args:
            schema (dict): The new schema to use.

        Raises:
            TypeError: If the schema is not a dictionary.
        """
        if schema is None:
            schema = {}
        if not isinstance(schema, dict):
            raise TypeError(f"schema must be a dictionary, not {type(schema)}.")
        self.schema = UserConfig.add_order(schema)


class ConfigEditor:
    """
    A class for managing the configuration editor, including handling user configurations,
    running the main entry point, starting and stopping the server, and cleaning up resources.

    Attributes:
        app_name (str): The name of the application. Defaults to "Config Editor".
        main_entry_runner (ProgramRunner): The runner for the main entry function.
        running (bool): A flag indicating whether the server is running.
        config_store (dict[str, UserConfig]): A dictionary storing user configuration objects.
        app (Flask): The Flask application instance for the web server.
        server (WSGIServer): The server instance handling incoming requests.
        server_thread (threading.Thread): The thread running the server.

    Methods:
        default_main_entry() -> ResultStatus:
            A default entry point function returning an undefined result.

        __init__(app_name: str = "Config Editor", main_entry: Callable | None = None) -> None:
            Initializes a new instance of ConfigEditor with the specified application name and main entry function.

        delete_user_config(user_config_name: str) -> None:
            Deletes a user configuration by its name from the configuration store.

        add_user_config(user_config: UserConfig, replace: bool = False) -> None:
            Adds a new user configuration to the configuration store. Optionally replaces an existing configuration.

        get_user_config_names() -> list[str]:
            Returns a list of names of all user configurations in the configuration store.

        get_user_config(user_config_name: str) -> UserConfig:
            Retrieves a user configuration by its name from the configuration store.

        launch_main_entry() -> ResultStatus:
            Launches the main entry point function and returns its result status.

        stop_server() -> None:
            Stops the running server.

        start_server() -> None:
            Starts the server to serve requests.

        clean_up() -> None:
            Gracefully shuts down the server, restores output streams, and waits for remaining threads to stop.

        run(host="localhost", port=80) -> None:
            Starts the web server and runs the configuration editor, opening it in a web browser.
    """

    def __init__(
        self,
        app_name: str = "Config Editor",
        main_entry: Callable | None = None,
    ) -> None:
        """
        Initializes a new instance of ConfigEditor with the specified application name and main entry function.

        Args:
            app_name (str): The name of the application (defaults to "Config Editor").
            main_entry (Callable | None): The main entry function to run (defaults to None, using the default main entry).

        Raises:
            TypeError: If `app_name` is not a string or `main_entry` is not callable.
            ValueError: If `app_name` is an empty string.
            KeyError: If trying to add or replace a UserConfig that already exists when `replace=False`.
        """
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

    @staticmethod
    def default_main_entry() -> None:
        """
        A default entry point function.

        Returns:
            ResultStatus: A result indicating the main entry is undefined.
        """
        return ResultStatus(False, "Main entry is undefined.")

    def add_user_config(
        self,
        user_config: UserConfig,
        replace: bool = False,
    ) -> None:
        """
        Adds a new user configuration to the configuration store. Optionally replaces an existing configuration.

        Args:
            user_config (UserConfig): The user configuration to add.
            replace (bool): Whether to replace an existing configuration with the same name (defaults to False).

        Raises:
            TypeError: If `user_config` is not a UserConfig object.
            KeyError: If the configuration name already exists and `replace=False`.
        """
        if not isinstance(user_config, UserConfig):
            raise TypeError(
                f"user_config must be a UserConfig object, not {type(user_config)}."
            )
        user_config_name = user_config.get_name()
        if user_config_name in self.config_store and not replace:
            raise KeyError(f"Config {user_config_name} already exists.")
        self.config_store[user_config_name] = user_config

    def delete_user_config(self, user_config_name: str) -> None:
        """
        Deletes a user configuration by its name from the configuration store.

        Args:
            user_config_name (str): The name of the user configuration to delete.

        Raises:
            KeyError: If no configuration with the specified name is found in the configuration store.
        """
        if user_config_name in self.config_store:
            del self.config_store[user_config_name]
        else:
            raise KeyError(f"Config {user_config_name} not found.")

    def get_user_config_names(self) -> list[str]:
        """
        Returns a list of names of all user configurations in the configuration store.

        Returns:
            list[str]: A list of user configuration names.
        """
        return list(self.config_store.keys())

    def get_user_config(self, user_config_name: str) -> UserConfig:
        """
        Retrieves a user configuration by its name from the configuration store.

        Args:
            user_config_name (str): The name of the user configuration to retrieve.

        Returns:
            UserConfig: The user configuration object corresponding to the given name.

        Raises:
            KeyError: If no configuration with the specified name is found in the configuration store.
        """
        if user_config_name in self.config_store:
            return self.config_store[user_config_name]
        else:
            raise KeyError(f"Config {user_config_name} not found.")

    def launch_main_entry(self) -> ResultStatus:
        """
        Launches the main entry point function and returns its result status.

        Returns:
            ResultStatus: The result status returned by running the main entry function.
        """
        return self.main_entry_runner.run()

    def stop_server(self) -> None:
        """
        Stops the running server by setting the `running` flag to False.
        """
        self.running = False

    def start_server(self) -> None:
        """
        Starts the server to serve incoming requests by calling `serve_forever` on the server instance.
        """
        self.server.serve_forever()

    def clean_up(self) -> None:
        """
        Gracefully shuts down the server, restores output streams, and waits for remaining threads to stop.
        This function ensures that all resources are cleaned up before exiting the program.
        """
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
        """
        Starts the web server and runs the configuration editor, opening it in a web browser.

        Args:
            host (str): The host to run the server on (defaults to "localhost").
            port (int): The port to bind the server to (defaults to 80).

        Raises:
            ValueError: If no UserConfig objects are added to the configuration editor before running.
        """
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

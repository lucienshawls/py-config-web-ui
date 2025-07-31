# pyConfigWebUI

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/lucienshawls/py-config-web-ui)
[![Build Status](https://github.com/lucienshawls/py-config-web-ui/actions/workflows/release.yml/badge.svg)](https://github.com/lucienshawls/py-config-web-ui/actions/workflows/release.yml)
[![License](https://img.shields.io/github/license/lucienshawls/py-config-web-ui)](LICENSE)
[![Latest Release Tag](https://img.shields.io/github/v/release/lucienshawls/py-config-web-ui)](https://github.com/lucienshawls/py-config-web-ui/releases/latest)
[![Latest PyPI Version](https://img.shields.io/pypi/v/configwebui-lucien.svg)](https://pypi.org/project/configwebui-lucien/)

A simple web-based configuration editor for Python applications.

This package provides tools for editing configuration files
in a user-friendly web interface.

Package on PyPI: [configwebui-lucien · PyPI](https://pypi.org/project/configwebui-lucien/)
## What It Does

**ConfigWebUI** is a lightweight and intuitive web-based configuration editor designed for Python applications. It allows developers to quickly generate user-friendly configuration interfaces from JSON schemas, enabling seamless configuration management without requiring users to understand the underlying file syntax.

### Features

- **Generate Configuration Interfaces Easily**: Provide a JSON schema, and ConfigWebUI generates a complete UI for configuration management.
- **Support for Profiles**: Manage multiple configuration profiles for the same schema. Easily switch between profiles without editing configurations each time.
- **Validation with Schema and Custom Logic**: The package validates configurations against the schema as users edit, ensuring data accuracy, and developers can specify additional backend validation to suit specific requirements.
- **Asynchronous Processing**: Supports asynchronous program execution with real-time status updates.
- **Interactive Terminal Output**: View and manage real-time program logs directly in the web UI.
- **Non-intrusive Integration**: Easily integrates into existing Python projects without interfering with their core functionality. The tool operates independently and does not alter the program's behavior unless explicitly used.
- **Seamless Fallback**: After applying this tool, your program can still run normally even if the web-based interface is not accessed. This ensures uninterrupted functionality in all scenarios.

### Screenshots
Screenshots are only available at the [GitHub repository](https://github.com/lucienshawls/py-config-web-ui) of this project.

- Automatically generate a web interface with only a schema

  ![Developers can automatically generate a web interface with only a schema](docs/general.png)

- Edit different profiles of different configurations with ease

  ![Users can edit different profiles of different configurations with ease](docs/save.png)

- Run the main programs and see the terminal output

  ![Users can run main programs and see the terminal output](docs/run.png)

## Try it out
To get an intuitive understanding of how to use this tool, you can do the following:

1. Clone this repository
    ```shell
    git clone https://github.com/lucienshawls/py-config-web-ui
    cd ./py-config-web-ui
    ```

2. Install dependencies in a virtual environment or a conda environment to avoid conflicts (or not).
    ```shell
    pip install -r ./requirements.txt
    ```

3. Run demo!
    ```shell
    python ./demo/demo_ui.py
    ```

4. Switch to your web browser

    If your browser does not pop up, visit the link that shows in your terminal.

5. Edit and save any config
6. See if your config has been saved to `./demo/config`
7. Click `Launch main program` (a submenu from `Save` in the navigation bar) and checkout the terminal output

    It should run `./demo/demo_main.py` and display some messages based on the config, just like running that Python file from the terminal.

## Architecture
As you see from the demo: with this package, your application can automatically generate a full-featured configuration editor UI from a schema. Here's how the architecture breaks down:

```
Config Schema --(defined in)--> UserConfig --(included in)--> ConfigEditor --(features)--> Local Web UI
```

### 0. Data Format
Developers can use `json`, `yaml`, `toml`, or any configuration format; just convert it to a Python `dict` when passing data into the system.

Internally, everything works with plain `dict` objects: the package requires only a `dict` on input and returns a `dict` on output.

That means, developers never need to worry about parsing or formatting when interacting with this package; just read your config from whatever source, supply it as a `dict`, and receive a `dict` back when saving.

### 1. Schema Input
Write a schema that defines the structure, defaults, types, and validation rules for each of your config. This schema becomes the single source of truth for generating the entire editor interface.

Learn more about schemas: [Json Schema](https://json-schema.org/)

### 2. UserConfig - Config Instance Wrapper
Each config schema and its corresponding config data are wrapped inside a `UserConfig` object. This class:

- Provides the schema for UI rendering;

- Validates user inputs based on the schema (including required fields, types, ranges, enums, etc.);

- Manages several profiles (they are based on the same schema; each stores an independent configuration);

- Connects to a developer-defined validation function for custom validations (aside from schema-based validations);

- Connects to a developer-defined save function to save configurations;

This modular design allows developers to manage multiple independent configurations within a single application.

### 3. ConfigEditor - Main Web UI Controller
The ConfigEditor is the application's core orchestrator. It:

- Starts a local HTTP server to serve the web interface.

- Manages one or more UserConfig instances.

- Automatically generates interactive UI forms from each schema.

- Handles the UI-to-backend workflows: loading configuration data, saving updates, and invoking actions like running scripts.

## Use it in your own project
### 1. Installation
Activate the python environment of your own project, and choose one of the installation methods:
1. Online installation from PyPI
```shell
pip install configwebui-lucien
```
2. Offline installtion from Github release

Download the `.whl` file from the [Latest Release](https://github.com/lucienshawls/py-config-web-ui/releases/latest). Install this using pip.

3. Make your own build
```shell
pip install setuptools setuptools-scm wheel build
python -m build -n --sdist --wheel
```
Then you can get the `.whl` file from `./dist/`. Install this using pip.

### 2. Import

In your python file, import this package:
```python
from configwebui import ConfigEditor, UserConfig, ResultStatus
```
or:

```python
from configwebui import *
```

They have exactly the same effect.

### 3. Integration
1. Preparation

    Generally, for each configuration, you will need:
    - `schema` of type `dict`
    - `extra_validation_function` which is `Callable`
    - `save function` which is `Callable`

    Additionally, you will need:
    - `main_entry_point` which is `Callable`

    In Detail:
    - Set up a function that verifies the config

        When user clicks the `Save` button on the webpage, the config will first pass the extra validations before it can be saved to the memory. You can set up your own validation function.

        Your function should take two positional arguments:
        - `name` of type `str`
        - `config` of type `dict` or `None`

        Your function should return a `ResultStatus` object or a `boolean` value. 

        If you choose the former, you can attach several error messages that the user can see on the webpage. For example, instantiate a `ResultStatus` object and set the messages:

        ```python
        from configwebui import *


        # True indicates a success
        res1 = ResultStatus(True, "Success!")

        # False indicates a failure
        res2 = ResultStatus(False, ["Failed!", "Incorrect format"])  # Message lists are also supported

        # Alternatively, you can also instantiate a ResultStatus object with no messages, and add messages or change status later.
        res3 = ResultStatus(True)
        res3.set_status(False)
        res3.add_message("message 1")
        ```

        This validation function is related to a specific `UserConfig` that you set up later.

        Example:
        ```python
        from configwebui import *


        def always_pass(
            config_name: str,
            config: dict | None,
        ) -> ResultStatus:
            # Instantiate a ResultStatus object with no messages, and set its status to True.
            res = ResultStatus(True)
            if False:
                # Just to show what to do when validation fails
                res.set_status(False)
                res.add_message("message 1")
                res.add_message("message 2")

            return res
        ```

    - Set up a function that saves config

        When user clicks the `Save` button on the webpage, and after the config passes extra validations, the config is saved to the memory immediately and your save function is then called in a separate thread.

        You can choose not to set the save function; however, if you do so, all edited configurations will only remain in memory and cannot be read, and will disappear when the program is restarted.

        Your function should take three positional arguments:
        - `user_config_name` of type `str`
        - `profile_name` of type `str`
        - `config` of type `dict`

        Parameter validation is not needed. It is guaranteed that the parameters satisfy your requirements.

        Return values are not needed either, because for now, the package does not read the result.

        This function is related to a specific `UserConfig` that you set up later.

        Example:
        ```python
        import json
        import os

        from configwebui import *


        def my_save(user_config_name: str, profile_name: str, config: dict):
            # You don't need to perform parameter validation
            os.makedirs(f"./config/{user_config_name}", exist_ok=True)
            with open(
                f"./config/{user_config_name}/{profile_name}.json", "w", encoding="utf-8"
            ) as f:
                json.dump(config, f, indent=4)
            print(config)
        ```

    - Set up a main entry point

        When user clicks `Launch main program` button on the webpage, your save function is called in a separate thread.

        Your function should take no positional arguments.

        Return values are not needed.

        This function is related to a specific `ConfigEditor` that you set up later.

        ATTENTION: Your main entry should be treated as an independent program that independently obtains configurations from the location where the configuration file is saved, and executes the code. Therefore, when the main entry is called, configuration-related parameters will not be passed in.

        Example:
        ```python
        import json
        import os


        def my_main_entry():
            print("======== This is main entry =======")
            if os.path.exists("config/myconfig.json"):
                with open("config/myconfig.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                print(config)
        ```

2. Fire it up

    Instantiate a `ConfigEditor` object, and add one or more `UserConfig`s to it:
    ```python
    import os

    from configwebui import *


    schema = {
        "title": "Example Schema",
        "type": "object",
        "properties": {
            "name": {"type": "string", "title": "Name"},
            "age": {"type": "integer", "title": "Age"},
            "is_student": {"type": "boolean"},
        },
    }  # You need to create this

    # Load the config from file and set initial values
    def my_load(user_config_name: str, profile_name: str) -> dict:
        # Read from config/<user_config_name>/<profile_name>.json
        file_path = f"config/{user_config_name}/{profile_name}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = None
        return config


    # Create a ConfigEditor object
    config_editor = ConfigEditor(
        app_name="Trial",  # display name, is used in the webpage title
        main_entry=my_main_entry,  # optional, main entry point, make sure it can run in a thread.
    )

    # Maybe there are multiple configurations and profiles. You may use a for-loop to iterate all names (e.g., from file names of a specific directory.)

    # Create a UserConfig object
    cur_config_name = "user_info"
    cur_config_friendly_name = "User Info"
    cur_user_config = UserConfig(
        name=cur_config_name,  # identifier, "user_info"
        friendly_name=cur_config_friendly_name,  # display name, "User Info"
        schema=schema,  # schema
        extra_validation_func=always_pass,  # optional, extra validation function
        save_func=my_save,  # optional, save function
        default_profile_only=False,  # Defaults to False.
        # If True, this UserConfig contains only one default profile, and custom profiles are disabled.
    )

    cur_profile_name = "Alice"
    cur_config_from_file = my_load(
        cur_config_name,  # "user_info"
        cur_profile_name,  # "Alice"
    )

    cur_user_config.update_profile(
        name=cur_profile_name,  # "Alice"
        config=cur_config_from_file,
        skip_schema_validations=True,  # optional, skip schema validations this time only
        skip_extra_validations=True,  # optional, skip extra validations this time only
        save_file=False,  # Defaults to False
        # Usually, when users make a change to the config, update_profile will be called, and the changes are saved to both the memory and the file.
        # But now, saving to file is not necessary, since we just fetched the config from file.
    )

    # Add the UserConfig object to the ConfigEditor object
    config_editor.add_user_config(user_config=cur_user_config)
    ```

3. Run it

    Run the ConfigEditor!

    Example:
    ```python
    # Change the port to 5000 if you do not have enough permissions.
    config_editor.run(host="127.0.0.1", port=80)
    ```

## Acknowledgements
I would like to express my gratitude to the following projects and individuals for different scenarios and reasons:

- Front-end design:
  - JSON Editor: [JSON Schema Based Editor](https://github.com/json-editor/json-editor)
    - with version: `v2.15.2`
  - CSS: [Bootstrap · The most popular HTML, CSS, and JS library in the world.](https://getbootstrap.com/)
    - with version: `v5.3.3`
  - JavaScript Library: [jQuery](https://jquery.com/)
    - with version: `v3.7.1`
  - Icons: [Font Awesome](https://fontawesome.com/)
    - with version: `v5.15.4`
- Coding
  - Testing: My friend [Eric](https://github.com/EricWay1024)
    - for: providing valuable test feedback
  - Assistant: [ChatGPT](https://chatgpt.com/)
    - for: making things easier

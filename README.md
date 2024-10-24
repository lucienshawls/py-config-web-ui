# pyConfigWebUI

[![Build Status](https://github.com/lucienshawls/py-config-web-ui/actions/workflows/release.yml/badge.svg)](https://github.com/lucienshawls/py-config-web-ui/actions/workflows/release.yml)
[![License](https://img.shields.io/github/license/lucienshawls/py-config-web-ui)](LICENSE)
[![Latest Release Tag](https://img.shields.io/github/v/release/lucienshawls/py-config-web-ui)](https://github.com/lucienshawls/py-config-web-ui/releases/latest)
[![Latest PyPI Version](https://img.shields.io/pypi/v/configwebui-lucien.svg)](https://pypi.org/project/configwebui-lucien/)

A simple web-based configuration editor for Python applications.

This package provides tools for editing configuration files
in a user-friendly web interface.

Package on PyPI: [configwebui-lucien · PyPI](https://pypi.org/project/configwebui-lucien/)

## Try it out
To get an intuitive understanding of how to use this tool, you can do the following:

1. Clone this repository
```shell
git clone https://github.com/lucienshawls/py-config-web-ui
cd ./py-config-web-ui
```

2. Install dependencies in a virtual environment or a conda environment (to avoid conflicts)
```shell
pip install -r ./requirements.txt
```

3. Run demo!
```shell
python ./examples/demo.py
```

4. Switch to your web browser

If your browser does not pop up, visit the link that shows in your terminal.

5. Edit and save any config
6. See if your config has been saved to `./examples/config`
7. Click `Launch main program` (a submenu from `Save`) and checkout the terminal

It should output some messages based on your config.

## Use it in your own project
1. Install

In the environment of your own project, run:
```shell
pip install configwebui-lucien
```

2. Integrate

In your python file, import this package:
```python
from configwebui import ConfigEditor, UserConfig, ResultStatus
```
or:

```python
from configwebui import *
```

They have exactly the same effect.

3. Optional preparations

- Set up a function that varifies the config

When user clicks the `Save` button on the webpage, the config will first pass the extra validations before it can be saved to the memory. You can set up your own validation function.

Your function should take one positional argument, which is for the config itself (`config`).

Your function should return a `ResultStatus` object or a `boolean` value. If you choose the former, you can attach several error messages that the user can see on the webpage.

This function is related to a specific `UserConfig` that you set up later.

Example:
```python
def always_pass(config: dict | list) -> ResultStatus:
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

Your function should take one positional argument, which is for the config itself (`config`).

You can freely choose the type (`json`, `yaml`, `toml`, etc.) and save method of the configuration file.

Parameter validation is not needed. It is guaranteed that the parameters satisfy your requirements.

Return values are not needed either, because for now, the package does not read the result.

This function is related to a specific `UserConfig` that you set up later.

Example:
```python
import json
import os
def my_save(config: dict | list):
    # You don't need to perform parameter validation
    os.makedirs("./config", exist_ok=True)
    with open("config/myconfig.json", "w", encoding="utf-8") as f:
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
import os
import json
def my_main_entry():
    print("======== This is main entry =======")
    if os.path.exists("config/myconfig.json"):
        with open("config/myconfig.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        print(config)
```

4. Fire it up

Instantiate a `ConfigEditor` object, and add one or more config schema to it:
```python
import os
schema = {
    "title": "Example Schema",
    "type": "object",
    "properties": {
        "name": {"type": "string", "title": "Name"},
        "age": {"type": "integer", "title": "Age"},
        "is_student": {"type": "boolean"},
    },
}  # You need to create this
# Create a ConfigEditor object
config_editor = ConfigEditor(
    app_name="Trial",  # display name, is used in the webpage title
    main_entry=my_main_entry,  # optional, main entry point, make sure it can run in a thread.
)

# Create a UserConfig object
user_config = UserConfig(
    name="myconfig",  # identifier
    friendly_name="Main config",  # display name
    schema=schema,  # schema
    extra_validation_func=always_pass,  # optional, extra validation function
    save_func=my_save,  # optional, save function
)

# Load the config from file and set initial values (or not, as you wish)
def load_config(name: str) -> dict | list:
    file_path = f"config/{name}.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = None
    return config

config_from_file = load_config("myconfig")
if config_from_file is not None:
    user_config.set_config(
        config=config_from_file,
        skip_schema_validations=True,  # optional, skip schema validations this time only
        skip_extra_validations=True,  # optional, skip extra validations this time only
    )

# Add the UserConfig object to the ConfigEditor object
config_editor.add_user_config(user_config=user_config)
```

5. Run it

Run the ConfigEditor!

Example:
```python
# Change the port to 5000 if you do not have enough permissions.
config_editor.run(host="localhost", port=80)
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

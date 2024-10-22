# This is a demo of how to use the Config Editor

# ============== You won't need the code below ============== #
import os
import sys

EXAMPLE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(EXAMPLE_DIRECTORY))
# ============== You won't need the code above ============== #

from configwebui import ConfigEditor, ResultStatus, UserConfig
from pprint import pprint
import time
import json


user_config_names = {
    "config1": "Config 1: this is a very long name that eats up a lot of space",
    "config2": "Config 2: this name is not as long",
    "config3": "Config 3: short name",
}

# 0. Prepare the schema, save functions and extra validation functions
with open(f"{EXAMPLE_DIRECTORY}/schema/general.json", "r", encoding="utf-8") as f:
    schema = json.load(f)


# def always_fail(config) -> ResultStatus:
#     return ResultStatus(False, ["msg1", "This always fails"])


def always_pass(config) -> ResultStatus:
    return ResultStatus(True)


def mysave(name: str, config: dict | list) -> ResultStatus:
    # You don't need to perform parameter validation
    with open(f"{EXAMPLE_DIRECTORY}/config/{name}.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    pprint(config)
    # No blocking
    time.sleep(3)
    return ResultStatus(True)


def load_config(name: str) -> dict | list:
    file_path = f"{EXAMPLE_DIRECTORY}/config/{name}.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = None
    return config


def my_main_entry():
    print("\nThis is the main entry point. Make sure it can run in a thread.")
    for user_config_name in user_config_names:
        file_path = f"{EXAMPLE_DIRECTORY}/config/{user_config_name}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f'{config["name"]} is {config["age"]} years old.')


# 1. Initialize the Config Editor
config_editor = ConfigEditor(
    app_name="Aurora Config Editor",  # display name, is used in the webpage title
    main_entry=my_main_entry,  # main entry point, make sure it can run in a thread.
)

# 2. Add UserConfig objects to the Config Editor
for user_config_name, user_config_friendly_name in user_config_names.items():
    # Create a UserConfig object
    user_config = UserConfig(
        name=user_config_name,  # identifier
        friendly_name=user_config_friendly_name,  # display name
        schema=schema,  # schema
        extra_validation_func=always_pass,  # extra validation function
        save_func=mysave,  # save function
    )

    # Load the config from file and set initial values (or not, as you wish)
    config_from_file = load_config(user_config_name)
    if config_from_file is not None:
        user_config.set_config(
            config=config_from_file,
            skip_extra_validations=True,
            skip_schema_validations=True,
        )

    # Add the UserConfig object to the ConfigEditor
    config_editor.add_user_config(
        user_config=user_config,
    )

# 3. Launch the Config Editor!
config_editor.run(host="localhost", port=80)

print("Config Editor is terminated.")

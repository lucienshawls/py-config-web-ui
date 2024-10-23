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


# Decorator to pass the name to the validation/save function
# Useful when you have multiple configs that use similar functions
def process_with_name(name: str):
    def decorator(func):
        def wrapper(config: dict | list):
            return func(name, config)

        return wrapper

    return decorator


user_config_names = {
    "config1": "Config 1: this is a very long name that eats up a lot of space",
    "config2": "Config 2: this name is not as long",
    "config3": "Config 3: short name",
}

# 1. Prepare the schema, save functions and extra validation functions
# 1.1. Schema
with open(f"{EXAMPLE_DIRECTORY}/schema/general.json", "r", encoding="utf-8") as f:
    schema = json.load(f)


# 1.2. Custom validation function, will be decorated with process_with_name
def always_pass(name: str, config: dict | list) -> ResultStatus:
    # Instantiate a ResultStatus object with no messages, and set its status to True.
    res = ResultStatus(True)
    if False:
        # Just to show what to do when validation fails
        res.set_status(False)
        res.add_message("message 1")
        res.add_message("message 2")

    return res


# 1.3. Custom save function, will be decorated with process_with_name
def my_save(name: str, config: dict | list) -> ResultStatus:
    # You don't need to perform parameter validation
    with open(f"{EXAMPLE_DIRECTORY}/config/{name}.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    pprint(config)
    # No blocking
    time.sleep(3)
    return ResultStatus(True)


# 1.4. Load config from file
def load_config(name: str) -> dict | list:
    file_path = f"{EXAMPLE_DIRECTORY}/config/{name}.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = None
    return config


# 1.5. Main entry point
def my_main_entry() -> None:
    print("\nThis is the main entry point. Make sure it can run in a thread.")
    for user_config_name in user_config_names:
        file_path = f"{EXAMPLE_DIRECTORY}/config/{user_config_name}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f'{config["name"]} is {config["age"]} years old.')


# 2. Fire it up
# 2.1. Create a ConfigEditor object
config_editor = ConfigEditor(
    app_name="Aurora Config Editor",  # display name, is used in the webpage title
    main_entry=my_main_entry,  # main entry point, optional, make sure it can run in a thread.
)

# 2.2. Add UserConfig objects to the ConfigEditor object you created
for user_config_name, user_config_friendly_name in user_config_names.items():
    # Create a UserConfig object
    user_config = UserConfig(
        name=user_config_name,  # identifier
        friendly_name=user_config_friendly_name,  # display name
        schema=schema,  # schema
        extra_validation_func=process_with_name(user_config_name)(
            always_pass
        ),  # optional, custom extra validation function
        save_func=process_with_name(user_config_name)(
            my_save
        ),  # optional, custom save function
    )

    # Load the config from file and set initial values (or not, as you wish)
    config_from_file = load_config(user_config_name)
    if config_from_file is not None:
        user_config.set_config(
            config=config_from_file,
            skip_schema_validations=True,  # optional, skip schema validations this time only
            skip_extra_validations=True,  # optional, skip extra validations this time only
        )

    # Add the UserConfig object to the ConfigEditor
    config_editor.add_user_config(user_config=user_config)

# 3. Launch the Config Editor!

# Change the port to 5000 if you do not have enough permissions.
config_editor.run(host="localhost", port=80)

print("Config Editor is terminated.")

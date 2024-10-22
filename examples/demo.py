from configwebui import ConfigEditor, ResultStatus, UserConfig
from pprint import pprint
import time

user_config_names = {
    "config1": "Config 1: this is a very long name that eats up a lot of space",
    "config2": "Config 2: this name is not as long",
    "config3": "Config 3: short name",
}

schema = {
    "title": "Person",
    "type": "object",
    "required": ["name", "age", "gender"],
    # "additionalProperties": True,
    "properties": {
        "name": {
            "title": "Write down your Name",
            "type": "string",
            "description": "First and Last name",
            "minLength": 4,
            "default": "Jeremy Dorn",
        },
        "age": {"type": "integer", "default": 25, "minimum": 18, "maximum": 99},
        "favorite_color": {
            "type": "string",
            "format": "color",
            "title": "favorite color",
            "default": "#ffa500",
        },
        "gender": {"type": "string", "enum": ["male", "female", "other"]},
        "date": {"type": "string", "format": "date", "options": {"flatpickr": {}}},
        "location": {
            "type": "object",
            "title": "Location",
            "properties": {
                "city": {"type": "string", "default": "San Francisco"},
                "state": {"type": "string", "default": "CA"},
                "citystate": {
                    "type": "string",
                    "description": "This is generated automatically from the previous two fields",
                    "template": "{{city}}, {{state}}",
                    "watch": {"city": "location.city", "state": "location.state"},
                },
                "test": {
                    "type": "object",
                    "title": "Test",
                    "properties": {
                        "value": {"type": "integer", "default": 0},
                        "another_value": {"type": "integer", "default": 0},
                        "te": {
                            "type": "object",
                            "title": "Test",
                            "properties": {
                                "st": {"type": "integer", "default": 0},
                            },
                        },
                        "st": {"type": "integer", "default": 0},
                    },
                },
            },
        },
        "pets": {
            "type": "array",
            "format": "table",
            "title": "Pets",
            "uniqueItems": True,
            "items": {
                "type": "object",
                "title": "Pet",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["cat", "dog", "bird", "reptile", "other"],
                        "default": "dog",
                    },
                    "name": {"type": "string"},
                },
            },
            "default": [{"type": "dog", "name": "Walter"}],
        },
    },
}


def always_fail(config):
    return ResultStatus(False, ["msg1", "This always fails"])


def always_pass(config):
    return ResultStatus(True)


def mysave(config):
    # No blocking
    time.sleep(3)
    pprint(config)
    return ResultStatus(True)


def my_main_entry():
    print("This is the main entry point. Make sure it can run in a thread.")


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

    # Add the UserConfig object to the ConfigEditor
    config_editor.add_user_config(
        user_config=user_config,
    )

# 3. Launch the Config Editor!
config_editor.run(host="localhost", port=80)

print("Config Editor is terminated.")

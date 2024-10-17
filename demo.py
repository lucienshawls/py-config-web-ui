from configwebui import ConfigEditor, ResultStatus, UserConfig
from pprint import pprint

user_config_names = {
    "config1": "Config 1: this is a very long name that eats up a lot of space",
    "config2": "Config 2: this name is not as long",
    "config3": "Config 3: short name",
}

schema = {
    "title": "Person",
    "type": "object",
    # "required": ["name", "age", "date", "favorite_color", "gender", "location", "pets"],
    "properties": {
        "name": {
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


def mycheck(config):
    if config["value"] == 0:
        return ResultStatus(True)
    return ResultStatus(False, [])


config_editor = ConfigEditor(app_name="Aurora Config Editor")
for user_config_name, user_config_friendly_name in user_config_names.items():
    config_editor.set_user_config(
        user_config_name=user_config_name,
        user_config_schema=schema,
        user_config_friendly_name=user_config_friendly_name,
    )
config_editor.run(host="localhost", port=80)

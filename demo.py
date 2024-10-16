from configwebui import ConfigEditor, ResultStatus

user_config_names = {
    "config1": "Config 1: this is a very long name that eats up a lot of space",
    "config2": "Config 2: this name is not as long",
    "config3": "Config 3: short name",
}


def mycheck(config):
    if config["value"] == 0:
        return ResultStatus(True)
    return ResultStatus(False, [])


config_editor = ConfigEditor(app_name="Aurora Config Editor")
for user_config_name, user_config_friendly_name in user_config_names.items():
    config_editor.set_user_config(
        user_config_name=user_config_name,
        user_config_friendly_name=user_config_friendly_name,
    )
config_editor.run(host="[::]", port=80)

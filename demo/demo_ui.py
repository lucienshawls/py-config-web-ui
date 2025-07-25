import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.configwebui import ConfigEditor, UserConfig
from demo import demo_main

CONFIG_EDITOR = ConfigEditor(app_name="Demo UI", main_entry=demo_main.main)
USER_CONFIGS = {
    "user_credential": {
        "friendly_name": "User Credential",
        "schema_file": "demo/schema/user_credential.json",
    },
    "applicant_information": {
        "friendly_name": "Applicant Information",
        "schema_file": "demo/schema/applicant_information.json",
    },
    "reservation_detail": {
        "friendly_name": "Reservation Detail",
        "schema_file": "demo/schema/reservation_detail.json",
    },
}
MAIN_CONFIG = {
    "friendly_name": "Main Config",
    "schema_file": "demo/schema/main.json",
}


def update_main_schema(user_config_name: str):
    main_user_config = CONFIG_EDITOR.get_user_config("main")
    main_schema = main_user_config.get_schema()
    target_user_config = CONFIG_EDITOR.get_user_config(user_config_name)
    target_profile_names = target_user_config.get_profile_names()
    main_schema["properties"][user_config_name]["enum"] = target_profile_names
    main_user_config.set_schema(main_schema)


def save_json(user_config_name: str, profile_name: str, config: dict | None):
    if user_config_name == "main":
        file_path = f"demo/config/main.json"
    else:
        file_path = f"demo/config/{user_config_name}/{profile_name}.json"
    if config is None:
        os.remove(file_path)
    else:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    if user_config_name != "main":
        update_main_schema(user_config_name=user_config_name)


def load_profile(user_config_name: str):
    if user_config_name == "main":
        CONFIG_EDITOR.get_user_config("main").update_profile(
            name="Default",
            config=demo_main.load_json("demo/config/main.json"),
        )
    else:
        directory_path = f"demo/config/{user_config_name}"
        if not os.path.exists(directory_path):
            return
        for profile_file_name in os.listdir(f"demo/config/{user_config_name}"):
            CONFIG_EDITOR.get_user_config(user_config_name).update_profile(
                name=profile_file_name.split(".")[0],
                config=demo_main.load_json(f"{directory_path}/{profile_file_name}"),
                skip_schema_validations=True,
                skip_extra_validations=True,
            )


def ui():
    main_schema = demo_main.load_json(MAIN_CONFIG["schema_file"])
    main_user_config = UserConfig(
        name="main",
        friendly_name=MAIN_CONFIG["friendly_name"],
        schema=main_schema,
        save_func=save_json,
        default_profile_only=True,
    )
    CONFIG_EDITOR.add_user_config(user_config=main_user_config)
    for user_config_name, user_config_info in USER_CONFIGS.items():
        config_directory = f"demo/config/{user_config_name}"
        if os.path.exists(config_directory):
            main_schema["properties"][user_config_name]["enum"] = [
                file.split(".")[0] for file in os.listdir(config_directory)
            ]
        user_config = UserConfig(
            name=user_config_name,
            friendly_name=user_config_info["friendly_name"],
            schema=demo_main.load_json(user_config_info["schema_file"]),
            save_func=save_json,
        )
        CONFIG_EDITOR.add_user_config(user_config)
        load_profile(user_config_name)
        update_main_schema(user_config_name=user_config_name)

    CONFIG_EDITOR.get_user_config("main").update_profile(
        config=demo_main.load_json("demo/config/main.json")
    )
    CONFIG_EDITOR.run(host="127.0.0.1", port=80)


if __name__ == "__main__":
    ui()

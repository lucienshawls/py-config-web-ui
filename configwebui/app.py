from . import ConfigEditor, UserConfig
from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    send_from_directory,
    url_for,
    current_app,
    request,
)
from markupsafe import escape

ICON_CLASS = {
    "info": "fas fa-info-circle",
    "success": "fas fa-check-circle",
    "warning": "fas fa-exclamation-triangle",
    "danger": "fas fa-times-circle",
}
ICON = {
    category: f'<i class="{ICON_CLASS[category]}"></i>'
    for category in ICON_CLASS.keys()
}

main = Blueprint("main", __name__)


@main.route("/")
@main.route("/config")
@main.route("/config/<config_name>")
def index(config_name: str = None):
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    if config_name is None:
        current_user_config_name = current_config_editor.get_user_config_names()[0]
    else:
        if config_name not in current_config_editor.get_user_config_names():
            flash(
                f'<span>{ICON["danger"]}</span> <span>No such config: <strong>{escape(config_name)}</strong></span>',
                "danger",
            )
            return redirect(url_for("main.index"))
        current_user_config_name = config_name
    current_user_config_object = current_config_editor.get_user_config(
        user_config_name=current_user_config_name
    )
    profile_names = current_user_config_object.get_profile_names()
    if len(profile_names) == 0:
        current_user_config_object.add_profile(
            name=UserConfig.DEFAULT_PROFILE_NAME, save_file=True
        )
        current_profile_name = UserConfig.DEFAULT_PROFILE_NAME
    else:
        current_profile_name = profile_names[0]
    flash(
        f'<span>{ICON["info"]}</span> '
        f"<span>"
        f"You are currently editing: Profile "
        f'<a class="alert-link" href="/config/{escape(current_user_config_name)}/{escape(current_profile_name)}">'
        f"{escape(current_profile_name)}"
        f"</a> of "
        f'<a class="alert-link" href="/config/{escape(current_user_config_name)}">'
        f"{escape(current_user_config_object.get_friendly_name())}"
        f"</a>."
        f"</span>",
        "info",
    )
    return redirect(
        url_for(
            "main.user_config_page",
            user_config_name=current_user_config_name,
            profile_name=current_profile_name,
        )
    )


@main.route("/config/<user_config_name>")
def user_config_index(user_config_name: str):
    return redirect(url_for("main.index"))


@main.route("/config/<user_config_name>/<profile_name>", methods=["GET", "POST"])
def user_config_page(user_config_name: str, profile_name: str):
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    user_config_names = current_config_editor.get_user_config_names()
    if user_config_name not in user_config_names:
        flash(
            f'<span>{ICON["danger"]}</span> <span>No such config: <strong>{escape(user_config_name)}</strong></span>',
            "danger",
        )
        return redirect(url_for("main.index"))
    user_config_object = current_config_editor.get_user_config(
        user_config_name=user_config_name
    )
    if not user_config_object.has_profile(profile_name):
        flash(
            f'<span>{ICON["info"]}</span> '
            f"<span>"
            f"No such profile: <strong>{escape(profile_name)}</strong> in "
            f'<a class="alert-link" href="/config/{escape(user_config_name)}">'
            f"{escape(user_config_object.get_friendly_name())}"
            f"</a>."
            f"</span>",
            "danger",
        )
        return redirect(url_for("main.index"))
    return render_template(
        "index.html",
        title=current_app.config["app_name"],
        user_config_store=current_config_editor.config_store,
        profile_names=user_config_object.get_profile_names(),
        current_user_config_name=user_config_name,
        current_profile_name=profile_name,
    )


@main.route(
    "/api/config/<user_config_name>/<profile_name>",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
def user_config_api(user_config_name: str, profile_name: str):
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    user_config_names = current_config_editor.get_user_config_names()
    if user_config_name not in user_config_names:
        if request.method == "GET":
            return make_response(
                {
                    "success": False,
                    "messages": [
                        f"No such config: <strong>{escape(user_config_name)}</strong>"
                    ],
                    "config": {},
                    "schema": {},
                },
                404,
            )
        else:
            return make_response(
                {
                    "success": False,
                    "messages": [
                        f"No such config: <strong>{escape(user_config_name)}</strong>"
                    ],
                },
                404,
            )
    user_config_object = current_config_editor.get_user_config(
        user_config_name=user_config_name
    )
    if not user_config_object.has_profile(profile_name):
        if request.method == "GET":
            return make_response(
                {
                    "success": False,
                    "messages": [
                        f"No such profile: <strong>{escape(profile_name)}</strong>"
                    ],
                    "config": {},
                    "schema": {},
                },
                404,
            )
        else:
            return make_response(
                {
                    "success": False,
                    "messages": [
                        f"No such profile: <strong>{escape(profile_name)}</strong>"
                    ],
                },
                404,
            )

    if request.method == "GET":
        # Get
        return make_response(
            {
                "success": True,
                "messages": [""],
                "config": user_config_object.get_config(profile_name=profile_name),
                "schema": user_config_object.get_schema(),
            },
            200,
        )
    elif request.method == "POST":
        # Add
        data: dict[str, str] = request.get_json()
        res_add = user_config_object.add_profile(name=data["name"], save_file=True)
        if res_add.get_status():
            return make_response(
                {
                    "success": True,
                    "messages": [
                        f"New profile "
                        f'<a class="alert-link" href="/config/{escape(user_config_name)}/{escape(data["name"])}">'
                        f"{escape(data['name'])}"
                        f"</a> has been added to "
                        f'<a class="alert-link" href="/config/{escape(user_config_name)}">'
                        f"{escape(user_config_object.get_friendly_name())}"
                        f"</a> in memory."
                    ],
                },
                201,
            )
        else:
            return make_response(
                {
                    "success": False,
                    "messages": list(map(escape, res_add.get_messages())),
                },
                400,
            )
    elif request.method == "PUT":
        # Rename
        data: dict[str, str] = request.get_json()

        if profile_name == data["name"]:
            return make_response(
                {
                    "success": False,
                    "messages": ["No changes detected. Please provide a new name."],
                },
                400,
            )
        res_rename = user_config_object.rename_profile(
            old_name=profile_name, new_name=data["name"], save_file=True
        )
        if res_rename.get_status():
            for message in res_rename.get_messages():
                flash(
                    f'<span>{ICON["warning"]}</span> <span>{message}</span>',
                    "warning",
                )
            return make_response(
                {
                    "success": True,
                    "messages": [
                        f"Profile <strong>{escape(profile_name)}</strong> of "
                        f'<a class="alert-link" href="/config/{escape(user_config_name)}">'
                        f"{escape(user_config_object.get_friendly_name())}"
                        f"</a> has been renamed to "
                        f'<a class="alert-link" href="/config/{escape(user_config_name)}/{data["name"]}">'
                        f'{escape(data["name"])}'
                        f"</a>."
                    ],
                },
                200,
            )
        else:
            return make_response(
                {
                    "success": False,
                    "messages": list(map(escape, res_rename.get_messages())),
                },
                400,
            )
    elif request.method == "PATCH":
        # Update
        data: dict[str, str] = request.get_json()
        if "config" not in data:
            return make_response(
                {
                    "success": False,
                    "messages": ["No config data provided."],
                },
                400,
            )
        res_update = user_config_object.update_profile(
            name=profile_name, config=data["config"], save_file=True
        )
        if res_update.get_status():
            return make_response(
                {
                    "success": True,
                    "messages": [
                        f"Profile "
                        f'<a class="alert-link" href="/config/{escape(user_config_name)}/{data["name"]}">'
                        f'{escape(data["name"])}'
                        f"</a> of "
                        f'<a class="alert-link" href="/config/{escape(user_config_name)}">'
                        f"{escape(user_config_object.get_friendly_name())}"
                        f"</a> has been updated."
                    ],
                },
                200,
            )
        else:
            return make_response(
                {
                    "success": False,
                    "messages": list(map(escape, res_update.get_messages())),
                },
                400,
            )
    elif request.method == "DELETE":
        # Delete
        data: dict[str, str] = request.get_json()
        res_delete = user_config_object.delete_profile(
            name=profile_name, save_file=True
        )
        if res_delete.get_status():
            for message in res_delete.get_messages():
                flash(
                    f'<span>{ICON["warning"]}</span> <span>{message}</span>',
                    "warning",
                )
            return make_response(
                {
                    "success": True,
                    "messages": [
                        f"Profile <strong>{escape(profile_name)}</strong> of "
                        f'<a class="alert-link" href="/config/{escape(user_config_name)}">'
                        f"{escape(user_config_object.get_friendly_name())}"
                        f"</a> has been deleted."
                    ],
                },
                200,
            )
        else:
            return make_response(
                {
                    "success": False,
                    "messages": list(map(escape, res_delete.get_messages())),
                },
                400,
            )


@main.route("/api/launch")
def launch():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    res = current_config_editor.launch_main_entry()
    if res.get_status():
        return make_response(
            {
                "success": True,
                "messages": [
                    f"The main program has been successfully requested to run. "
                    f'<a href="#terminal-output-display" class="alert-link">'
                    f"Check it out below"
                    f"</a>.",
                ],
            },
            200,
        )
    else:
        return make_response(
            {
                "success": False,
                "messages": ["Main program is already running"],
            },
            503,
        )


@main.route("/api/shutdown")
def shutdown():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.stop_server()
    return make_response("", 204)


@main.route("/api/clear_terminal_output", methods=["POST"])
def clear_terminal_output():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.main_entry_runner.clear()
    return make_response("", 204)


@main.route("/api/get_terminal_output")
def get_terminal_output():
    recent_only = bool(int(request.args.get("recent_only", "0")))
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    res = current_config_editor.main_entry_runner.get_res()
    return make_response(
        {
            "success": True,
            "messages": list(map(escape, res.get_messages())),
            "state": res.get_status(),
            "has_warning": current_config_editor.main_entry_runner.has_warning(),
            "running": current_config_editor.main_entry_runner.is_running(),
            "combined_output": current_config_editor.main_entry_runner.get_combined_output(
                recent_only=recent_only
            ),
        },
        200,
    )


@main.route("/<path:path>")
def catch_all(path):
    if path == "favicon.ico":
        return send_from_directory("static/icon", "favicon.ico")
    if path[-1] == "/":
        return redirect(f"/{path[:-1]}")
    flash(
        f'<span>{ICON["danger"]}</span> <span>Page not found</span>',
        "danger",
    )
    return redirect(url_for("main.index"))

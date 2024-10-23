import sys
from . import ConfigEditor
from flask import Blueprint
from flask import flash, redirect, render_template, url_for, make_response
from flask import current_app, request


main = Blueprint("main", __name__)


@main.route("/")
@main.route("/config")
def index():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_user_config_name = current_config_editor.get_user_config_names()[0]
    current_user_config_object = current_config_editor.get_user_config(
        user_config_name=current_user_config_name
    )
    flash(
        f"You are currently editing: [{current_user_config_object.get_friendly_name()}]",
        "info",
    )
    return redirect(
        url_for("main.user_config_page", user_config_name=current_user_config_name)
    )


@main.route("/config/<user_config_name>", methods=["GET", "POST"])
def user_config_page(user_config_name):
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    user_config_names = current_config_editor.get_user_config_names()
    if user_config_name not in user_config_names:
        flash(f"No such config: <{user_config_name}>", "danger")
        return redirect(url_for("main.index"))
    else:
        return render_template(
            "index.html",
            title=current_app.config["app_name"],
            user_config_store=current_config_editor.config_store,
            current_user_config_name=user_config_name,
        )


@main.route("/api/config/<user_config_name>", methods=["GET", "POST"])
def user_config_api(user_config_name):
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    user_config_names = current_config_editor.get_user_config_names()
    if user_config_name not in user_config_names:
        if request.method == "GET":
            return make_response(
                {
                    "success": False,
                    "messages": f"No such config: <{user_config_name}>",
                    "config": {},
                    "schema": {},
                },
                400,
            )
        else:
            return {
                "success": False,
                "messages": [f"No such config: <{user_config_name}>"],
            }
    else:
        user_config_object = current_config_editor.get_user_config(
            user_config_name=user_config_name
        )
        if request.method == "GET":
            return make_response(
                {
                    "success": True,
                    "messages": [f"Config <{user_config_name}> found"],
                    "config": user_config_object.get_config(),
                    "schema": user_config_object.get_schema(),
                },
                200,
            )
        else:
            uploaded_config = request.json
            user_config_object = current_config_editor.get_user_config(
                user_config_name=user_config_name
            )
            res = user_config_object.set_config(config=uploaded_config)
            if res.get_status():
                user_config_object.save()
                return make_response(
                    {
                        "success": True,
                        "messages": [
                            f'[<a href="/config/{user_config_name}">{user_config_object.get_friendly_name()}</a>] has been saved'
                        ],
                    },
                    200,
                )
            else:
                messages = res.get_messages()
                if len(messages) == 0:
                    messages = ["Extra validation failed"]
                return make_response({"success": False, "messages": messages}, 400)


@main.route("/api/launch")
def launch():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.launch_main_entry()
    return make_response("", 204)


@main.route("/api/shutdown")
def shutdown():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.stop_server()
    return make_response("", 204)


@main.route("/<path:path>")
def catch_all(path):
    flash("Page not found", "danger")
    return redirect(url_for("main.index"))

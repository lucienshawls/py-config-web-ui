from . import ConfigEditor
from flask import Blueprint
from flask import flash, redirect, render_template, url_for, make_response
from flask import current_app, request


main = Blueprint("main", __name__)


@main.route("/")
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
        if request.method == "GET":
            flash(f"No such config: <{user_config_name}>", "danger")
            return redirect(url_for("main.index"))
        else:
            return {
                "success": False,
                "messages": [f"No such config: <{user_config_name}>"],
            }
    else:
        if request.method == "GET":
            return render_template(
                "index.html",
                title=current_app.config["app_name"],
                name_mod=(
                    ".min" if current_app.config["USE_MINIFIED_STATIC_FILES"] else ""
                ),
                user_config_store=current_config_editor.config_store,
                current_user_config_name=user_config_name,
            )
        else:
            uploaded_config = request.json
            user_config_object = current_config_editor.get_user_config(
                user_config_name=user_config_name
            )
            res = user_config_object.set_config(config=uploaded_config)
            if res.get_status():
                return make_response(
                    {
                        "success": True,
                        "messages": [
                            f"[{user_config_object.get_friendly_name()}] has been saved"
                        ],
                    },
                    200,
                )
            else:
                return make_response(
                    {"success": False, "messages": res.get_messages()}, 400
                )


@main.route("/greetings")
def greetings():
    print("Hello, World!")
    return render_template("index.html", title="Greetings")


@main.route("/shutdown")
def shutdown():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.stop()


@main.route("/<path:path>")
def catch_all(path):
    flash("Page not found", "danger")
    return redirect(url_for("main.index"))

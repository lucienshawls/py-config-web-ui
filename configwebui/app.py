from . import ConfigEditor
from flask import render_template, Blueprint, current_app, redirect, url_for

main = Blueprint("main", __name__)


@main.route("/")
def index():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_user_config_name = current_config_editor.get_user_config_names()[0]
    return redirect(
        url_for("main.user_config_page", user_config_name=current_user_config_name)
    )


@main.route("/<user_config_name>")
def user_config_page(user_config_name):
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    user_config_names = current_config_editor.get_user_config_names()
    if user_config_name not in user_config_names:
        return redirect(url_for("main.index"))
    return render_template(
        "index.html",
        title=current_app.config["app_name"],
        name_mod=".min" if current_app.config["USE_MINIFIED_STATIC_FILES"] else "",
        user_config_store=current_config_editor.config_store,
        current_user_config_name=user_config_name,
    )


@main.route("/greetings")
def greetings():
    print("Hello, World!")
    return render_template("index.html", title="Greetings")


@main.route("/shutdown")
def shutdown():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.stop()

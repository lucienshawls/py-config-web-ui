from . import ConfigEditor
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    url_for,
    make_response,
    current_app,
    request,
)
from markupsafe import escape


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
        f"You are currently editing: "
        f'<a class="alert-link" href="/config/{escape(current_user_config_name)}">'
        f"{escape(current_user_config_object.get_friendly_name())}"
        f"</a>",
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
        flash(f"No such config: <strong>{escape(user_config_name)}</strong>", "danger")
        return redirect(url_for("main.index"))
    else:
        return render_template(
            "index.html",
            title=current_app.config["app_name"],
            user_config_store=current_config_editor.config_store,
            current_user_config_name=user_config_name,
        )


@main.route("/api/config/<user_config_name>", methods=["GET", "PATCH"])
def user_config_api(user_config_name):
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
    else:
        user_config_object = current_config_editor.get_user_config(
            user_config_name=user_config_name
        )
        if request.method == "GET":
            return make_response(
                {
                    "success": True,
                    "messages": [""],
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
                if user_config_object.save().get_status():
                    return make_response(
                        {
                            "success": True,
                            "messages": [
                                f'<a class="alert-link" '
                                f'href="/config/{escape(user_config_name)}">'
                                f"{escape(user_config_object.get_friendly_name())}"
                                f"</a> has been saved to memory.",
                                f"A data-saving script has been successfully requested to run. "
                                f'<a href="#save-output" class="alert-link">'
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
                            "messages": [
                                f'<a class="alert-link" '
                                f'href="/config/{escape(user_config_name)}">'
                                f"{escape(user_config_object.get_friendly_name())}"
                                f"</a> has been saved <strong>ONLY</strong> to memory.",
                                "Last save data-saving script has not finished yet, please try again later.",
                            ],
                        },
                        503,
                    )

            else:
                messages = res.get_messages()
                if len(messages) == 0:
                    messages = ["Submitted config did not pass all validations"]
                return make_response({"success": False, "messages": messages}, 400)


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
                    f'<a href="#main-output" class="alert-link">'
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


@main.route("/api/config/<user_config_name>/get_save_output")
def get_save_output(user_config_name):
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    user_config_names = current_config_editor.get_user_config_names()
    if user_config_name not in user_config_names:
        return make_response(
            {
                "success": False,
                "messages": [
                    f"No such config: <strong>{escape(user_config_name)}</strong>"
                ],
                "output": "",
            },
            404,
        )
    else:
        user_config_object = current_config_editor.get_user_config(
            user_config_name=user_config_name
        )
        res = user_config_object.save_func_runner.get_res()
        return make_response(
            {
                "success": True,
                "messages": res.get_messages(),
                "state": res.get_status(),
                "has_warning": user_config_object.save_func_runner.has_warning(),
                "running": user_config_object.save_func_runner.is_running(),
                "combined_output": user_config_object.save_func_runner.get_combined_output(
                    recent_only=True
                ),
            },
            200,
        )


@main.route("/api/get_main_output")
def get_main_output():
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    res = current_config_editor.main_entry_runner.get_res()
    return make_response(
        {
            "success": True,
            "messages": res.get_messages(),
            "state": res.get_status(),
            "has_warning": current_config_editor.main_entry_runner.has_warning(),
            "running": current_config_editor.main_entry_runner.is_running(),
            "combined_output": current_config_editor.main_entry_runner.get_combined_output(
                recent_only=True
            ),
        },
        200,
    )


@main.route("/<path:path>")
def catch_all(path):
    flash("Page not found", "danger")
    return redirect(url_for("main.index"))

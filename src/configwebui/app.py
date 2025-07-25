"""
Flask web application for managing and interacting with user configurations.

This application provides a set of routes and APIs for handling user configurations
through a web interface and API endpoints. It allows users to view, add, update,
rename, and delete profiles within configurations. Additionally, it includes endpoints
for launching, stopping, and interacting with a main entry process, as well as handling
terminal output and application shutdowns.

Routes:
    - /config/<user_config_name>: Redirects to the main configuration page.
    - /config/<user_config_name>/<profile_name>: Displays a specific profile page for a user configuration.
    - /api/config/<user_config_name>/<profile_name>: API endpoint for getting, adding, updating, renaming, and deleting profiles.
    - /api/launch: API endpoint to launch the main program.
    - /api/shutdown: API endpoint to shut down the application server.
    - /api/clear_terminal_output: API endpoint to clear the terminal output.
    - /api/get_terminal_output: API endpoint to get the terminal output.
    - /<path:path>: Catch-all route for undefined paths, handles redirects for paths with trailing slashes and provides error handling for non-existent pages.

Classes:
    - ConfigEditor: A class for managing user configurations, profiles, and interacting with the main program.

Usage:
    The application is built using Flask and provides both a user interface for
    configuration management and an API for programmatic access to configuration data
    and terminal output. It includes handling of configuration profiles and offers
    functionality to execute and manage a main entry process, such as launching and
    stopping the server, and retrieving terminal output.

    Flash messages are used to provide feedback to the user, and the application
    supports dynamic content rendering based on configuration data.
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from markupsafe import escape

from . import ConfigEditor, UserConfig

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
@main.route("/config/<user_config_name>")
def index(user_config_name: str = None):
    """
    Handle requests to display the main configuration editor page.

    This function checks if a specific configuration name is provided via the
    URL. If no configuration name is provided, it defaults to the first available
    user configuration. If a configuration name is provided, it verifies if the
    configuration exists. It also checks if there are any profiles associated with
    the selected configuration, and if none exist, a default profile is created.
    Finally, it redirects the user to the page for editing the selected profile
    within the chosen configuration.

    Args:
        user_config_name (str, optional): The name of the user configuration to edit.
            If not provided, defaults to the first user config.

    Returns:
        flask.Response: A redirect to the user configuration page for editing the selected profile.

    Notes:
        An error message is flashed if the provided config name does not exist.
        An info message is flashed with the current profile being edited.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    if user_config_name is None:
        current_user_config_name = current_config_editor.get_user_config_names()[0]
    else:
        if user_config_name not in current_config_editor.get_user_config_names():
            flash(
                f'<span>{ICON["danger"]}</span> <span>No such config: <strong>{escape(user_config_name)}</strong></span>',
                "danger",
            )
            return redirect(url_for("main.index"))
        current_user_config_name = user_config_name
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
    """
    Redirect to the main configuration editor page with the specified user configuration name.

    This function handles requests to view a specific user configuration page.
    It redirects the user to the main configuration index page, passing the provided
    user configuration name as a URL parameter.

    Args:
        user_config_name (str): The name of the user configuration that is being accessed.

    Returns:
        flask.Response: A redirect response to the main configuration editor page,
            including the user configuration name as a URL parameter.
    """
    return redirect(url_for("main.index", user_config_name=user_config_name))


@main.route("/config/<user_config_name>/<profile_name>", methods=["GET", "POST"])
def user_config_page(user_config_name: str, profile_name: str):
    """
    Handle displaying and processing the user configuration page for a specific profile.

    This function manages requests to view or modify a specific profile within a user configuration.
    If the configuration or profile doesn't exist, it flashes an error message and redirects
    the user back to the main configuration index page. If both exist, it renders the configuration
    page with the details of the specified profile.

    Args:
        user_config_name (str): The name of the user configuration being accessed.
        profile_name (str): The name of the profile within the user configuration.

    Returns:
        flask.Response:
            - If the user configuration or profile does not exist, the function returns a redirect
              to the main index page with an error message.
            - If the configuration and profile are valid, it renders the 'index.html' template
              with the user configuration details and profile information.
    """
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
            f'<span>{ICON["danger"]}</span> '
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
    """
    Handle API requests for user configuration profiles. Supports the following methods:
    - GET: Retrieve the configuration and schema of a profile.
    - POST: Add a new profile to the user configuration.
    - PUT: Rename an existing profile.
    - PATCH: Update the configuration of an existing profile.
    - DELETE: Delete an existing profile from the user configuration.

    Args:
        user_config_name (str): The name of the user configuration being accessed.
        profile_name (str): The name of the profile within the user configuration.

    Returns:
        flask.Response: A JSON response indicating the success or failure of the requested operation.
            - For GET: Returns the profile configuration and schema.
            - For POST, PUT, PATCH, DELETE: Returns a success or error message with status code 200 or 400.
    """
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
    """
    Handle the API request to launch the main program.

    This route interacts with the ConfigEditor to attempt to launch the main program.
    If the program is already running, a failure response is returned. If the program is successfully
    launched, a success response with a link to the terminal output is provided.

    Args:
        None

    Returns:
        flask.Response: A Flask response indicating the success or failure of the main program launch.
    """
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
    """
    Handle the API request to shut down the server.

    This route interacts with the ConfigEditor to stop the server. After stopping the server,
    it returns an empty response with a 204 status code indicating the successful shutdown.

    Args:
        None

    Returns:
        flask.Response: A Flask response indicating the success of the shutdown operation.
        - Success (204): The server has been successfully shut down.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.stop_server()
    return make_response("", 204)


@main.route("/api/clear_terminal_output", methods=["POST"])
def clear_terminal_output():
    """
    Handle the API request to clear the terminal output.

    This route interacts with the ConfigEditor to clear the stored terminal output
    from the main entry runner. After clearing the output, it returns an empty response
    with a 204 status code indicating the successful action.

    Args:
        None

    Returns:
        flask.Response: A Flask response indicating the success of the clear action.
        - Success (204): The terminal output has been successfully cleared.
    """
    current_config_editor: ConfigEditor = current_app.config["ConfigEditor"]
    current_config_editor.main_entry_runner.clear()
    return make_response("", 204)


@main.route("/api/get_terminal_output")
def get_terminal_output():
    """
    Handle the API request to retrieve the terminal output.

    This route retrieves the output of the main entry runner, including
    messages, state, warnings, running status, and combined output. The
    "recent_only" query parameter can be used to filter for recent output.

    Args:
        None

    Returns:
        flask.Response: A Flask response containing the terminal output information.
    """
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
    """
    Handle all requests for undefined routes.

    This route catches all incoming requests that do not match any predefined
    route. It handles requests for favicon.ico, redirects requests with a
    trailing slash, and shows an error message for non-existent pages.

    Args:
        path (str): The URL path of the requested resource.

    Returns:
        flask.Response: A Flask response depending on the type of request:
            - If the request is for "favicon.ico", it returns the favicon from
              the static directory.
            - If the path ends with a slash, it redirects to the same path
              without the trailing slash.
            - For all other requests, it flashes a "Page not found" error
              message and redirects to the homepage.
    """
    if path == "favicon.ico":
        return send_from_directory("static/icon", "favicon.ico")
    if path[-1] == "/":
        return redirect(f"/{path[:-1]}")
    flash(
        f'<span>{ICON["danger"]}</span> <span>Page not found</span>',
        "danger",
    )
    return redirect(url_for("main.index"))

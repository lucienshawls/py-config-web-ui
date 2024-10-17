import os
import requests
import re
from configwebui.config import AppConfig
from urllib.parse import urljoin

STATIC_FILE_DIRECTORY = "configwebui/static"
USE_MINIFIED_STATIC_FILES = AppConfig.USE_MINIFIED_STATIC_FILES
NAME_MOD = ".min" if USE_MINIFIED_STATIC_FILES else ""


def save_file(url: str, path: str) -> None:
    r = requests.get(url)
    with open(path, "wb") as f:
        f.write(r.content)


def download_json_editor() -> None:
    save_file(
        f"https://cdn.jsdelivr.net/npm/@json-editor/json-editor@latest/dist/jsoneditor{NAME_MOD}.js",
        f"{STATIC_FILE_DIRECTORY}/js/jsoneditor{NAME_MOD}.js",
    )


def download_bootstrap() -> None:
    save_file(
        f"https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim{NAME_MOD}.js",
        f"{STATIC_FILE_DIRECTORY}/js/jquery.slim{NAME_MOD}.js",
    )
    save_file(
        f"https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle{NAME_MOD}.js",
        f"{STATIC_FILE_DIRECTORY}/js/bootstrap.bundle{NAME_MOD}.js",
    )
    save_file(
        f"https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap{NAME_MOD}.css",
        f"{STATIC_FILE_DIRECTORY}/css/bootstrap{NAME_MOD}.css",
    )


def download_fontawesome() -> None:
    # No minified version of fontawesome
    fontawesome_url = f"https://use.fontawesome.com/releases/v5.6.1/css/all.css"

    # Download latest fontawesome
    save_file(fontawesome_url, f"{STATIC_FILE_DIRECTORY}/css/fontawesome.all.css")

    # Download fontawesome webfonts
    with open(f"{STATIC_FILE_DIRECTORY}/css/fontawesome.all.css", "r") as f:
        fontawesome_css = f.read()
    font_names_raw = re.findall(r"url\(\.\./webfonts/(.*?)\)", fontawesome_css)
    font_names = set()
    for font_name_raw in font_names_raw:
        font_name = re.search(r"^(.*?)(\?.*|#.*)?$", font_name_raw).group(1)
        font_names.add(font_name)
    for font_name in font_names:
        save_file(
            urljoin(fontawesome_url, f"../webfonts/{font_name}"),
            f"{STATIC_FILE_DIRECTORY}/webfonts/{font_name}",
        )


def download_files() -> None:

    os.makedirs(f"{STATIC_FILE_DIRECTORY}/js", exist_ok=True)
    os.makedirs(f"{STATIC_FILE_DIRECTORY}/css", exist_ok=True)
    os.makedirs(f"{STATIC_FILE_DIRECTORY}/webfonts", exist_ok=True)

    download_json_editor()
    download_bootstrap()
    download_fontawesome()


if __name__ == "__main__":
    download_files()

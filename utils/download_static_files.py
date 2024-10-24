import os
import re
import requests
from urllib.parse import urljoin

STATIC_FILE_DIRECTORY = "configwebui/static"
VERSION = {
    "json-editor": "2.15.2",
    "bootstrap": "5.3.3",
    "jquery": "3.7.1",
    "fontawesome": "5.15.4",
}


def save_file(url: str, path: str) -> None:
    r = requests.get(url)
    with open(path, "wb") as f:
        f.write(r.content)


def download_json_editor() -> None:
    save_file(
        f'https://cdn.jsdelivr.net/npm/@json-editor/json-editor@{VERSION["json-editor"]}/dist/jsoneditor.min.js',
        f"{STATIC_FILE_DIRECTORY}/js/jsoneditor.min.js",
    )


def download_bootstrap() -> None:
    save_file(
        f'https://cdn.jsdelivr.net/npm/jquery@{VERSION["jquery"]}/dist/jquery.slim.min.js',
        f"{STATIC_FILE_DIRECTORY}/js/jquery.slim.min.js",
    )
    save_file(
        f'https://cdn.jsdelivr.net/npm/bootstrap@{VERSION["bootstrap"]}/dist/js/bootstrap.bundle.min.js',
        f"{STATIC_FILE_DIRECTORY}/js/bootstrap.bundle.min.js",
    )
    save_file(
        f'https://cdn.jsdelivr.net/npm/bootstrap@{VERSION["bootstrap"]}/dist/css/bootstrap.min.css',
        f"{STATIC_FILE_DIRECTORY}/css/bootstrap.min.css",
    )


def download_fontawesome() -> None:
    fontawesome_url = (
        f'https://use.fontawesome.com/releases/v{VERSION["fontawesome"]}/css/all.css'
    )
    save_file(fontawesome_url, f"{STATIC_FILE_DIRECTORY}/css/fontawesome.all.css")

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

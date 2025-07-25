import os

STATIC_DIRECTORY = "src/configwebui/static"
CUSTOM_STATIC_FILES_BY_DIRECTORY = {
    "css": ["index.css"],
    "icon": [
        "apple-touch-icon.png",
        "favicon-96x96.png",
        "favicon.ico",
        "favicon.svg",
        "site.webmanifest",
        "web-app-manifest-192x192.png",
        "web-app-manifest-512x512.png",
    ],
    "js": ["index.js"],
}


def main():
    for subdirectory in [
        subdirectory
        for subdirectory in os.listdir(STATIC_DIRECTORY)
        if os.path.isdir(os.path.join(STATIC_DIRECTORY, subdirectory))
    ]:
        custom_static_files = CUSTOM_STATIC_FILES_BY_DIRECTORY.get(subdirectory, [])
        for file in os.listdir(os.path.join(STATIC_DIRECTORY, subdirectory)):
            if file not in custom_static_files:
                os.remove(os.path.join(STATIC_DIRECTORY, subdirectory, file))
                print(f"Removed {os.path.join(STATIC_DIRECTORY, subdirectory, file)}")


if __name__ == "__main__":
    main()

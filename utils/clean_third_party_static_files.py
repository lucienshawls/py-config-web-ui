import os

STATIC_DIRECTORY = "configwebui/static"
CUSTOM_STATIC_FILES_BY_DIRECTORY = {
    "css": ["index.css"],
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

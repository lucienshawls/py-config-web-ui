import shutil


def clean_build():
    for directory in ["dist", "configwebui_lucien.egg-info"]:
        shutil.rmtree(directory, ignore_errors=True)


if __name__ == "__main__":
    clean_build()

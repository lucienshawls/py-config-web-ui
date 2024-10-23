import os


class AppConfig:
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24).hex()

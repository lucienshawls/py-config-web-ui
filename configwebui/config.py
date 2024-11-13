import os


class AppConfig:
    DEBUG = False
    JSON_AS_ASCII = False
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24).hex()

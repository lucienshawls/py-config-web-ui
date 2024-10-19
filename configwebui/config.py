import os


def generate_secret_key():
    return os.urandom(24).hex()


class AppConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY") or generate_secret_key()

from os import path, environ

# Constants
TITLE = "Fuzed"
CONFIG_PATH = path.join(environ["APPDATA"], TITLE, "config.cfg")

AUTH_LEVELS = ["Super-user",
               "Administrator",
               "Standard"]

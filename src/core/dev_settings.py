# SECURITY WARNING: keep the secret key used in production secret!
# You should change this key before you go live!
import os

DEBUG = True
SECRET_KEY = "uxprsdhk^gzd-r=_287byolxn)$k6tsd8_cepl^s^tms2w1qrv"

# This is the default redirect if no other sites are found.
DEFAULT_HOST = "https://www.example.org"
EMAIL_BACKEND = (
    os.environ.get(
        "JANEWAY_EMAIL_BACKEND",
    )
    or "django.core.mail.backends.console.EmailBackend"
)

URL_CONFIG = "path"  # path or domain

MIDDLEWARE = (
    "utils.middleware.TimeMonitoring",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)
INSTALLED_APPS = [
    "debug_toolbar",
]


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
}

HIJACK_LOGIN_REDIRECT_URL = "/manager/"
HIJACK_USERS_ENABLED = True

ENABLE_FULL_TEXT_SEARCH = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "log_file"],
    },
    "formatters": {
        "default": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "P:%(process)d T:%(thread)d %(message)s",
        },
        "coloured": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)s %(asctime)s %(module)s "
            "P:%(process)d T:%(thread)d %(message)s",
            "log_colors": {
                "DEBUG": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "coloured",
            "stream": "ext://sys.stdout",
        },
        "log_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 1,
            "filename": os.path.join(PROJECT_DIR, "logs/janeway.log"),
            "formatter": "default",
        },
    },
    "loggers": {
        "django.db.backends": {
            #'level': 'DEBUG',
            "level": "WARNING",
            "handlers": ["console", "log_file"],
            "propagate": False,
        },
    },
}

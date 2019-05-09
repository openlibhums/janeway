# SECURITY WARNING: keep the secret key used in production secret!
# You should change this key before you go live!
DEBUG = True
SECRET_KEY = 'uxprsdhk^gzd-r=_287byolxn)$k6tsd8_cepl^s^tms2w1qrv'

# This is the default redirect if no other sites are found.
DEFAULT_HOST = 'https://www.example.org'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

URL_CONFIG = 'path'  # path or domain

MIDDLEWARE_CLASSES = (
    'utils.middleware.TimeMonitoring',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
)
INSTALLED_APPS = [
    'debug_toolbar',
    'django_nose',
    'hijack',
    'compat',
]


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
}
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

HIJACK_LOGIN_REDIRECT_URL = '/manager/'
HIJACK_LOGOUT_REDIRECT_URL = '/manager/'

# SECURITY WARNING: keep the secret key used in production secret!
# You should change this key before you go live!
DEBUG = True
SECRET_KEY = 'uxprsdhk^gzd-r=_287byolxn)$k6tsd8_cepl^s^tms2w1qrv'

# This is the default redirect if no other sites are found.
DEFAULT_HOST = 'https://www.example.org'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

URL_CONFIG = 'path'  # path or domain
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MIDDLEWARE_CLASSES = ('utils.middleware.TimeMonitoring',)

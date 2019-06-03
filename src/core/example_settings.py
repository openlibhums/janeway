
# SECURITY WARNING: keep the secret key used in production secret!
# You should change this key before you go live!
SECRET_KEY = 'uxprsdhk^gzd-r=_287byolxn)$k6tsd8_cepl^s^tms2w1qrv'

# This is the default redirect if no other sites are found.
DEFAULT_HOST = 'https://www.example.org'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
LOGIN_REDIRECT_URL = '/user/profile/'

# CATCHA_TYPE should be either 'simple_math' or 'recaptcha' to enable captcha
#fields, otherwise disabled
CAPTCHA_TYPE = 'recaptcha'
RECAPTCHA_PRIVATE_KEY = ''
RECAPTCHA_PUBLIC_KEY = ''

# ORCID Settings
ENABLE_ORCID = True
ORCID_API_URL = 'http://pub.orcid.org/v2.1'
ORCID_URL = 'https://orcid.org/oauth/authorize'
ORCID_TOKEN_URL = 'https://pub.orcid.org/oauth/token'
SOCIAL_AUTH_ORCID_KEY = ''
SOCIAL_AUTH_ORCID_SECRET = ''
SOCIAL_AUTH_ORCID_SANDBOX_KEY = ''
SOCIAL_AUTH_ORCID_SANDBOX_SECRET = ''

# Default Langague
LANGUAGE_CODE = 'en'

URL_CONFIG = 'path'  # path or domain

DATABASES = {
    'default': {
        #Example ENGINEs:
        #   sqlite:     'django.db.backends.sqlite
        #   mysql:      'django.db.backends.sqlite
        #   postgres:   'django.db.backends.postgres
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'},
    }
}


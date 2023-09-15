
# SECURITY WARNING: keep the secret key used in production secret!
# You should change this key before you go live!
SECRET_KEY = 'uxprsdhk^gzd-r=_287byolxn)$k6tsd8_cepl^s^tms2w1qrv'

# This is the default redirect if no other sites are found.
DEFAULT_HOST = 'https://www.example.org'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
LOGIN_REDIRECT_URL = '/user/profile/'

INTERNAL_IPS = [
    '127.0.0.1',
    '192.168.65.2',
    '192.168.65.1',
]

#%%% print (5+7)

# CATCHA_TYPE should be either 'simple_math' or 'recaptcha' to enable captcha
#fields, otherwise disabled
CAPTCHA_TYPE = 'recaptcha'

# If using recaptcha complete the following
RECAPTCHA_PRIVATE_KEY = ''
RECAPTCHA_PUBLIC_KEY = ''

# If using hcaptcha complete the following:
HCAPTCHA_SITEKEY = ''
HCAPTCHA_SECRET = ''

# ORCID Settings
ENABLE_ORCID = True
ORCID_API_URL = 'http://pub.orcid.org/v1.2_rc7/'
ORCID_URL = 'https://orcid.org/oauth/authorize'
ORCID_TOKEN_URL = 'https://pub.orcid.org/oauth/token'
ORCID_CLIENT_SECRET = ''
ORCID_CLIENT_ID = ''

# Default Langague
LANGUAGE_CODE = 'en'

URL_CONFIG = 'path'  # path or domain

DATABASES = {
    'default': {
        #Example ENGINEs:
        #   sqlite:     'django.db.backends.sqlite
        #   mysql:      'django.db.backends.mysql
        #   postgres:   'django.db.backends.postgresql
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'janeway',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'db.janeway.internal',
        'PORT': '5432',
    }
}


# OIDC Settings
ENABLE_OIDC = False
OIDC_SERVICE_NAME = 'OIDC Service Name'
OIDC_RP_CLIENT_ID = ''
OIDC_RP_CLIENT_SECRET = ''
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_OP_AUTHORIZATION_ENDPOINT = ""
OIDC_OP_TOKEN_ENDPOINT = ""
OIDC_OP_USER_ENDPOINT = ""
OIDC_OP_JWKS_ENDPOINT = ''


ENABLE_FULL_TEXT_SEARCH = False # Read the docs before enabling full text

# Model used for indexing full text files
CORE_FILETEXT_MODEL = "core.FileText"  # Use "core.PGFileText" for Postgres

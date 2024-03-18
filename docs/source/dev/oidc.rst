Open ID Connect (OIDC)
======================
Support for Open ID Connect has been added in 1.4.2 of Janeway. This guide aims to assist you in setting up OIDC with Janeway. Janeway makes use of the (`Mozilla Django OIDC <https://github.com/mozilla/mozilla-django-oidc>`_) package.

If you are upgrading from 1.4.1 to 1.4.2+ ensure you reinstall all requirements so that any required packages are installed.

Settings
--------
The majority of changes required to get OIDC working in Janeway are in your settings files.

By default OIDC is disabled in janeway_global_settings module. You can overwrite this in your local settings file with the following:

::

    # OIDC Settings
    ENABLE_OIDC = True
    OIDC_SERVICE_NAME = 'Your SSO Service Name'
    OIDC_RP_CLIENT_ID = 'your-client-name'
    OIDC_RP_CLIENT_SECRET = ''
    OIDC_RP_SIGN_ALGO = 'RS256'
    OIDC_OP_AUTHORIZATION_ENDPOINT = "https://auth.example.org/auth/realms/REALMNAME/protocol/openid-connect/auth"
    OIDC_OP_TOKEN_ENDPOINT = "https://auth.example.org/auth/realms/REALMNAME/protocol/openid-connect/token"
    OIDC_OP_USER_ENDPOINT = "https://auth.example.org/auth/realms/REALMNAME/protocol/openid-connect/userinfo"
    OIDC_OP_JWKS_ENDPOINT = 'https://auth.example.org/auth/realms/REALMNAME/protocol/openid-connect/certs'
    OIDC_LOGOUT_URL = 'https://auth.example.orgg/auth/realms/REALMNAME/protocol/openid-connect/logout'

    if ENABLE_OIDC:
        MIDDLEWARE_CLASSES += (
            'mozilla_django_oidc.middleware.SessionRefresh',
        )

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'utils.oidc.JanewayOIDCAB',
    )

.. note:: All of the urls above are examples derived from a Keycloak instance. You can get the real URLs by using your service providers .well-known url which will look something like:     https://exmaple/org/.well-known/openid-configuration. You can get your Client ID and Secret from your service provider admin console or can request one from your technical staff. If you use RS256 for OIDC_RP_SIGN_ALGO you must also complete OIDC_OP_JWKS_ENDPOINT otherwise login will fail.

New Accounts
------------
When a user without an account on Janeway logs in a new active account is generated for them with their Email address as the django username, first name and last name are also copied.

Session Refresh
---------------
It is essential that the SessionRefresh middleware is enabled so that Janeway can detect if the login status of the remote user changes.

Detecting Users
---------------
You can detect if a user logged in via OIDC by checking `request.user.is_oidc` this will return `True` if the user logged in with OIDC, note it will not exist if the user did not.

.. note:: Although OIDC can be used for Authentication (login) it is not used for Authorisation (who can access what resource). Remote roles/groups will make no difference to the Janeway install at this time.

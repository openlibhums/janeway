from django.contrib.auth.models import BaseUserManager
from django.shortcuts import reverse

from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


def generate_oidc_username(email):
    return BaseUserManager.normalize_email(email)


class JanewayOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    @property
    def success_url(self):
        # Pull the next url from the session or settings--we don't need to
        # sanitize here because it should already have been sanitized.
        next_url = self.request.session.get('oidc_login_next', None)
        self.request.session.is_oidc = True
        return next_url or reverse('website_index')


class JanewayOIDCAB(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(JanewayOIDCAB, self).create_user(claims)

        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.is_active = True
        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.is_active = True
        user.save()

        return user


def logout_url(request):
    return reverse('website_index')

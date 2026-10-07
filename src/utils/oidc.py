from django.contrib.auth.models import BaseUserManager
from django.shortcuts import redirect, reverse
from django.utils.http import urlencode

from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
)
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


def generate_oidc_username(email):
    return BaseUserManager.normalize_email(email)


class JanewayOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    @property
    def success_url(self):
        # Pull the next url from the session or settings--we don't need to
        # sanitize here because it should already have been sanitized.
        next_url = self.request.session.get("oidc_login_next", None)
        self.request.session.is_oidc = True
        return next_url or reverse("website_index")


class JanewayOIDCAuthenticationRequestView(OIDCAuthenticationRequestView):
    """Starts every OIDC login at the press level.

    The identity provider only accepts the callback URLs registered with it,
    so redirect_uri must never carry a journal or repository path prefix.
    Requests made under a path mode prefix are redirected to the same view at
    the press level, with a next url that returns the user to the site they
    started on once the login is complete.
    """

    def get(self, request):
        if request.path == request.path_info:
            return super().get(request)

        next_url = request.GET.get("next") or reverse("website_index")
        return redirect(
            "{}?{}".format(request.path_info, urlencode({"next": next_url}))
        )


class JanewayOIDCAB(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(JanewayOIDCAB, self).create_user(claims)

        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.is_active = True
        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.is_active = True
        user.save()

        return user


def logout_url(request):
    return reverse("website_index")

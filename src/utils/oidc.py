from django.contrib.auth.models import BaseUserManager
from django.shortcuts import reverse
from django.urls import get_script_prefix, set_script_prefix

from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
)
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.middleware import SessionRefresh


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
    """Builds the OIDC authorize request from the site root.

    This view has two responsibilities.

    First, journals served in path mode set a script prefix (e.g.
    /journal_code), which would otherwise leak into redirect_uri and fail the
    identity provider's exact-match check against its registered callback
    URLs. The prefix is reset for the duration of the authorize request and
    restored afterwards.

    Second, the callback is always served at press level, so with no next url
    in the session it would fall back to the press index and strand users who
    began logging in on a journal or repository site. When no explicit next
    url has been supplied we record the current site's index instead, so
    users return to where they started. An explicit next url, which the
    library has already validated, always takes precedence.
    """

    def get(self, request):
        # Resolved before the prefix is reset so that it is site aware,
        # giving /<journal_code>/ in path mode and / at press level.
        default_next = reverse("website_index")
        prefix = get_script_prefix()
        set_script_prefix("/")
        try:
            response = super().get(request)
        finally:
            set_script_prefix(prefix)

        if not request.session.get("oidc_login_next"):
            request.session["oidc_login_next"] = default_next

        return response


class JanewaySessionRefresh(SessionRefresh):
    """A SessionRefresh that builds its re-auth redirect from the site root.

    Deployments that want silent OIDC session refresh should list this class
    in MIDDLEWARE instead of mozilla_django_oidc.middleware.SessionRefresh,
    after core.middleware.SiteSettingsMiddleware: the stock middleware
    rebuilds redirect_uri under the journal script prefix in path mode, which
    identity providers reject as an unregistered redirect URI, looping until
    e.g. Entra's AADSTS50196.

    Resetting the prefix also keeps the exempt OIDC endpoints, which the
    stock middleware reverses once and caches, at their press-level paths
    rather than whichever journal prefix the first request happened to carry.
    """

    def process_request(self, request):
        prefix = get_script_prefix()
        set_script_prefix("/")
        try:
            return super().process_request(request)
        finally:
            set_script_prefix(prefix)

    def is_refreshable_url(self, request):
        """Exempts the OIDC endpoints however they were reached.

        In path mode request.path keeps the journal prefix (e.g.
        /journal_code/oidc/logout/) while the exempt urls are press-level
        paths, so the stock check alone would refresh on the OIDC endpoints
        themselves. SiteSettingsMiddleware strips the prefix from
        request.path_info, so that is checked as well.
        """
        if not super().is_refreshable_url(request):
            return False
        return request.path_info not in self.exempt_urls and not any(
            pattern.match(request.path_info) for pattern in self.exempt_url_patterns
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

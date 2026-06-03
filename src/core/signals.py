__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def migrate_accessibility_mode_preference(sender, request, user, **kwargs):
    """Carry an anonymous accessibility-mode preference onto the account.

    When an anonymous visitor enables accessibility mode the preference is
    held in the session. On login we persist it to Account.accessibility_mode
    and always clear the session flag, so the session can never shadow the
    account value. Without this the session flag would keep the mode active
    regardless of the account preference, making it impossible to disable.
    """
    if request is None:
        return

    session = getattr(request, "session", None)
    if session is None:
        return

    had_session_preference = bool(session.pop("accessibility_mode", False))
    if had_session_preference and not user.accessibility_mode:
        user.accessibility_mode = True
        user.save(update_fields=["accessibility_mode"])

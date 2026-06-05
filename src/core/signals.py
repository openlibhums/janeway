__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from core.const import Sentinel


@receiver(user_logged_in)
def migrate_accessibility_mode_preference(sender, request, user, **kwargs):
    """Carry an anonymous accessibility-mode preference onto the account.

    The anonymous preference is held in the session. The key is only present
    when the visitor explicitly toggled the mode, and its value records the
    explicit choice (``True`` for on, ``False`` for off). If the key is absent
    the visitor never touched the control and the account preference stands.

    On login we therefore distinguish "explicit toggle" from "untouched":

    * Untouched (key absent): apply nothing; the account value wins.
    * Explicit on/off (key present): that choice wins and is written back to
      Account.accessibility_mode, including an explicit off that disables a
      previously enabled account preference.

    The session flag is always cleared so it can never shadow the account
    value on subsequent requests.
    """
    if request is None:
        return

    session = getattr(request, "session", None)
    if session is None:
        return

    value = session.pop("accessibility_mode", Sentinel.UNSET)
    if value is Sentinel.UNSET:
        return

    explicit = bool(value)
    if user.accessibility_mode != explicit:
        user.accessibility_mode = explicit
        user.save(update_fields=["accessibility_mode"])

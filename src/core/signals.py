__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from core import logic


@receiver(user_logged_in)
def migrate_accessibility_mode_preference(sender, request, user, **kwargs):
    """Carry explicit anonymous reader preferences onto the account on login.

    Runs the generic preference store's login migration for every registered
    descriptor (accessibility mode, reading options, ...). Each preference is
    held in the session only when the visitor explicitly changed it; on login an
    explicit choice wins and is written back to the account, while an untouched
    preference leaves the account value standing.

    * Untouched (key absent): apply nothing; the account value wins.
    * Explicit on/off (key present): that choice wins and is written back to
      including an explicit off that disables a
      previously enabled account preference.
    """
    logic.migrate_session_preferences(request, user)

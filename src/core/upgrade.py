"""
Routines for handling Janeway version upgrades.
"""

__copyright__ = "Copyright 2025 Open Library of Humanties"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.apps import apps
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from utils.logic import get_janeway_version


@receiver(post_migrate)
def version_change_signal(sender, **kwargs):
    """Signal handler that commits Janeway version changes"""
    if sender.name == "utils":
        # Ensure we only log the version change once after any migrations
        # affecting the model have run
        Version = apps.get_model("utils", "Version")
        Version.objects.log_version_change(get_janeway_version())

from django.core.management.base import BaseCommand
from django.utils import translation

from utils import install


class Command(BaseCommand):
    """
    Loads permissions onto settings. Individual setting permissions were introduced
    into Janeway as part of version 1.5. Each setting in a setting JSON file should have
    an attribute called "editable_by" which contains a list of role slugs that can
    edit that setting. Here is an example:

    "editable_by": [
        "editor", "journal-manager"
    ]

    When loaded by the load_default_settings command and no editable_by attribute is
    found then Janeway will maintain the status quo and set journal-manager and editor
    as the two roles that can edit a setting.
    """

    help = "Loads the new setting permission settings onto Janeway."

    def handle(self, *args, **options):
        install.load_permissions()

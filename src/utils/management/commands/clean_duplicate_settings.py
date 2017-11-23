from django.core.management.base import BaseCommand

from core import models as core_models


class Command(BaseCommand):
    """
    A management command that removes duplicate named settings in the core.Setting model. This is useful when you have
    corrupted the settings table by running early dev versions of Janeway.
    """

    help = "Deletes duplicate settings."

    def handle(self, *args, **options):
        """Delete duplicate named settings in the core.Setting model.

        :param args: None
        :param options: None
        :return: None
        """
        settings = core_models.Setting.objects.all()

        for row in settings:
            if core_models.Setting.objects.filter(name=row.name).count() > 1:
                row.delete()

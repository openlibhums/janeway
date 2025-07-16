from django.core.management.base import BaseCommand

from press import models as press_models


class Command(BaseCommand):
    """A management command to move the press site to a new URL"""

    help = "Moves your press to a new URL. Does not move journals."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument("new_url")

    def handle(self, *args, **options):
        """Moves your press to a new URL."

        :param args: None
        :param options: Dictionary containing a 'new_url' string to which the press will be relocated
        :return: None
        """
        p = press_models.Press.get_press(None)
        p.domain = options["new_url"]
        p.save()

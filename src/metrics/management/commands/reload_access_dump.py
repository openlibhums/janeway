import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers


class Command(BaseCommand):
    """
    A management command that reloads a dumped access list and removes the totals from the historic views.
    """

    help = "Reloads a dumped access list and removes the totals from the historic views."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--file', default=False)

    def handle(self, *args, **options):
        """Reloads a dumped access list and removes the totals from the historic views.

        :param args: None
        :param options: None
        :return: None
        """

        file_path = os.path.join(settings.BASE_DIR,
                                 'files',
                                 'data_backup',
                                 options.get('file'),
                                 'article_accesses.json')

        with open(file_path) as file:
            data = file.read()

        for obj in serializers.deserialize("json", data):
            obj.save()

            if obj.object.type == 'view':
                obj.object.article.historicarticleaccess.remove_one_view()
            elif obj.object.type == 'download':
                obj.object.article.historicarticleaccess.remove_one_download()

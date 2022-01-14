from django.core.management.base import BaseCommand

from repository import install, models

class Command(BaseCommand):
    """ A management command to update repository settings."""

    help = "Installs a journal."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--short_name', default=False)
        parser.add_argument('--force', action='store_true', default=False)

    def handle(self, *args, **options):
        """Updates repository settings for a given repository.

        :param args: None
        :param options: Dictionary containing keys '--short_name', '--journal_code' and '--base_url'. If any of these
        are not provided, they will be requested via raw_input. --force will overwrite all settings.
        :return: None
        """
        short_name = options.get('short_name', None)
        force = options.get('force')

        if short_name:
            repos = models.Repository.objects.filter(short_name=short_name)
        else:
            repos = models.Repository.objects.all()

        if not repos:
            print('No repositories found.')
            exit()

        for repo in repos:
            print("Processing {}".format(repo.name))
            install.load_settings(repo, force)
            repo.save()

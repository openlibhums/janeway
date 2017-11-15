from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import translation

from press import models as press_models
from journal import models as journal_models
from utils.install import update_settings, update_license
from submission import models as submission_models


class Command(BaseCommand):
    """
    Installs a press and oe journal for Janeway.
    """

    help = "Installs a press and oe journal for Janeway."

    def handle(self, *args, **options):
        """Installs Janeway

        :param args: None
        :param options: None
        :return: None
        """
        call_command('makemigrations', 'sites')
        call_command('migrate')
        print("Please answer the following questions.\n")
        translation.activate('en')

        test_one = press_models.Press.objects.all()
        if not test_one:
            press = press_models.Press()
            press.name = input('Press name: ')
            press.domain = input('Press domain: ')
            press.main_contact = input('Press main contact (email): ')
            press.save()

        print("Thanks! We will now set up out first journal.\n")
        journal = journal_models.Journal()
        journal.code = input('Journal #1 code: ')
        journal.domain = input('Journal #1 domain: ')
        journal.save()

        print("Installing settings fixtures... ", end="")
        update_settings(journal, management_command=False)
        print("[okay]")
        print("Installing license fixtures... ", end="")
        update_license(journal, management_command=False)
        print("[okay]")
        print("Installing role fixtures")
        call_command('loaddata', 'utils/install/roles.json')

        journal.name = input('Journal #1 name: ')
        journal.description = input('Journal #1 description: ')
        journal.save()
        journal.setup_directory()

        submission_models.Section.objects.language('en').get_or_create(journal=journal,
                                                                       number_of_reviewers=2,
                                                                       name='Article',
                                                                       plural='Articles')

        print("Thanks, Journal #1 has been saved.\n")

        call_command('show_configured_journals')
        call_command('sync_journals_to_sites')
        call_command('build_assets')
        print("Installing plugins.")
        call_command('install_plugins')
        print("Installing Cron jobs")
        call_command('install_cron')

        print('Create a super user.')
        call_command('createsuperuser')
        print('Open your browser to your new journal domain {domain}/install/ to continue this setup process.'.format(domain=journal.domain))

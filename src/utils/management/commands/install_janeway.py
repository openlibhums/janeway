import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.utils import translation

from press import models as press_models
from journal import models as journal_models
from utils.install import (
        update_issue_types,
        update_settings,
        update_xsl_files,
)
from submission import models as submission_models

ROLES_RELATIVE_PATH = 'utils/install/roles.json'


class Command(BaseCommand):
    """
    Installs a press and oe journal for Janeway.
    """

    help = "Installs a press and oe journal for Janeway."

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Rolls back the transaction resulting from this command',
        )

    def handle(self, *args, **options):
        """Installs Janeway

        :param args: None
        :param options: None
        :return: None
        """
        call_command('migrate')
        print("Please answer the following questions.\n")
        translation.activate('en')
        with transaction.atomic():
            test_one = press_models.Press.objects.all()
            if not test_one:
                press = press_models.Press()
                press.name = input('Press name: ')
                press.domain = input('Press domain: ')
                press.main_contact = input('Press main contact (email): ')
                press.save()

            print("Thanks! We will now set up out first journal.\n")
            update_xsl_files()
            journal = journal_models.Journal()
            journal.code = input('Journal #1 code: ')
            if settings.URL_CONFIG == 'domain':
                journal.domain = input('Journal #1 domain: ')
            journal.save()

            print("Installing settings fixtures... ", end="")
            update_settings(journal, management_command=False)
            print("[okay]")
            print("Installing issue types fixtures... ", end="")
            update_issue_types(journal, management_command=False)
            print("[okay]")
            print("Installing role fixtures")
            roles_path = os.path.join(settings.BASE_DIR, ROLES_RELATIVE_PATH)
            print('Installing default settings')
            call_command('load_default_settings')
            call_command('loaddata', roles_path)
            journal.name = input('Journal #1 name: ')
            journal.description = input('Journal #1 description: ')
            journal.save()
            journal.setup_directory()

            print("Thanks, Journal #1 has been saved.\n")

            call_command('show_configured_journals')
            call_command('build_assets')
            print("Installing plugins.")
            call_command('install_plugins')
            print("Installing Cron jobs")
            try:
                call_command('install_cron')
            except FileNotFoundError:
                self.stderr.write("Error Installing cron")
            print('Create a super user.')
            call_command('createsuperuser')
            print('Open your browser to your new journal domain '
                '{domain}/install/ to continue this setup process.'.format(
                    domain=journal.domain
                        if settings.URL_CONFIG == 'domain'
                        else '{}/{}'.format(
                            press.domain, journal.code)
                )
            )
            if options['dry_run'] is True:
                print("This was a --dry-run, rolling back...")
                raise SystemExit()
        print(JANEWAY_ASCII)


JANEWAY_ASCII = """
===========================================================================================================================================================
=============================================================================================================================================================
===============================================================================================================================================================
===============================================================================================================================================================
===============================================================================================================================================================
===============================================================================================================================================================
==============================================================================================================================================================
=============================================================================================================================================================
==========================================================================================================================================================
==========================================
=========,======   ,   ==   ===========,
=========   =  ,   ,   ==   ===,======*
========   =   ,   ,   ==   =    =====        ========        =====       ====       ===   ============   ===       ===       ===      =====     ===       ===
=======   =    =   ,   ==   ==   =====             ===       ======       ======     ===   ===            ====     =====     ===      =======     ====   ====
======   =,   ==   ,   ==   ==   =====             ===      ===  ===      ========   ===   ===             ====   ======    ====     ===  ====     ==== ====
=====    =   ===   ,   ==   ===   ====             ===     ===    ===     ===  ====  ===   ============     ===   === ===   ===     ====   ===       =====
====    =   ====   ,   ==   ===   ====  ===        ===    ===      ===    ====   =======   ===               === ===  ==== ===     ====     ===       ===
====   =   =====   ,   ==   ===   ====  ===       ====   ==============   ===     ======   ===               =======   =======    ==============      ===
===   =    =====   ,   ==   ====   ===   ============   ====        ====  ===       ====   ============       =====     =====    ====         ===     ===
=================  ,   ==   ==== =====     ========    ====          ==== ===         ==   ============        ===       ===    ====          ====    ===
"""


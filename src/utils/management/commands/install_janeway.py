import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.utils import translation
from django.core.exceptions import ImproperlyConfigured

from core import models as core_models
from press import models as press_models
from journal import models as journal_models
from utils.install import (
        update_issue_types,
        update_settings,
        update_xsl_files,
)

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
        parser.add_argument(
            '--use-defaults',
            action='store_true',
            dest='use_defaults',
            default=False,
            help='Avoids requesting user input and uses default details',
        )

    def handle(self, *args, **options):
        """Installs Janeway

        :param args: None
        :param options: dict
        :return: None
        """

        # As of v1.4 USE_I18N must be enabled.
        if not settings.USE_I18N:
            raise ImproperlyConfigured("USE_I18N must be enabled from v1.4 of Janeway.")
        use_defaults = options["use_defaults"]

        call_command('migrate')
        print("Please answer the following questions.\n")
        translation.activate('en')
        with transaction.atomic():
            test_one = press_models.Press.objects.all()
            if not test_one:
                press = press_models.Press()
                if use_defaults:
                    press.name = "press"
                    press.domain = "localhost"
                    press.main_contant= "dev@noemail.com"
                else:
                    press.name = input('Press name: ')
                    press.domain = input('Press domain: ')
                    press.main_contact = input('Press main contact (email): ')
                press.save()

            print("Thanks! We will now set up our first journal.\n")
            print("Installing settings and XSL fixtures... ", end="")
            update_xsl_files()
            update_settings()
            print("[okay]")
            journal = journal_models.Journal()
            if use_defaults:
                journal.code = "journal"
            else:
                journal.code = input('Journal #1 code: ')
                journal.domain = input('Journal #1 domain (Optional): ')
            journal.save()
            print("Installing issue types fixtures... ", end="")
            update_issue_types(journal, management_command=False)
            print("[okay]")
            print("Installing role fixtures")
            roles_path = os.path.join(settings.BASE_DIR, ROLES_RELATIVE_PATH)
            print('Installing default settings')
            call_command('load_default_settings')
            call_command('loaddata', roles_path)
            if use_defaults:
                journal.name = "Test Journal"
                journal.description = "Test Journal"
            else:
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
            if not use_defaults:
                call_command('createsuperuser')
            print('Open your browser to your new journal domain '
                '{domain}/install/ to continue this setup process.'.format(
                    domain=journal.domain
                        if journal.domain
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

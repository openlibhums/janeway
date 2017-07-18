from django.core.management.base import BaseCommand

from django.contrib.sites import models as site_models
from journal import models as journal_models
from press import models as press_models


class Command(BaseCommand):
    """A management command to show existing journal, press and site configuration."""

    help = "Shows configured journal URLs."

    def handle(self, *args, **options):
        """ Show existing configuration of journals, press and sites.

        :param args: None
        :param options: None
        :return: None
        """
        p = press_models.Press.get_press(None)

        print("Press:")
        print("Press [{0}]: {1}".format(p.name, p.domain))

        journals = journal_models.Journal.objects.all()

        print("\nJournals:")
        for journal in journals:
            print('Journal with ID {0} [{1}]: {2}'.format(journal.id, journal.name, journal.domain))

        site_list = site_models.Site.objects.all()

        print("\nSites:")
        for site in site_list:
            print('Site with ID {0} [{1}]: {2}'.format(site.id, site.name, site.domain))

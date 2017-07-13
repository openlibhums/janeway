from django.core.management.base import BaseCommand
from django.contrib.sites import models as site_models
from django.utils import translation

from journal import models as journal_models
from press import models as press_models


class Command(BaseCommand):
    """A management command to synchronize all configured journals and press settings to sites."""

    help = "Synchronizes configured journal and press URLs with sites."

    def handle(self, *args, **options):
        """Synchronizes journals and presses with sites.

        :param args: None
        :param options: None
        :return: None
        """

        translation.activate('en')
        site_models.Site.objects.all().delete()

        journals = journal_models.Journal.objects.all()

        print("Journals:")
        for journal in journals:
            print(journal.name, journal.domain)
            new_site = site_models.Site(name=journal.code, domain=journal.domain)
            new_site.save()
            print('Journal with ID {0} [{1}]: {2}. SYNCED.'.format(journal.id, journal.name, journal.domain))

        print("\nPress:")
        p = press_models.Press.get_press(None)

        new_site = site_models.Site(name=p.name, domain=p.domain)
        new_site.save()
        print("Press [{0}]: {1}. SYNCED.".format(p.name, p.domain))

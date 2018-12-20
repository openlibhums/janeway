from itertools import chain

from django.core.management.base import BaseCommand

from journal.models import Journal
from press.models import Press
from core.models import DomainAlias

class Command(BaseCommand):
    """
    A management command that prints a set of A records for your install
    """

    help = "Prints A records in plain text."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--serverip', default=False)

    def handle(self, *args, **options):
        sites = chain(
                Journal.objects.all(),
                Press.objects.all(),
                DomainAlias.objects.all(),
        )

        for site in sites:
            print('{domain}. IN A {ipaddress}'.format(domain=site.domain, ipaddress=options.get('serverip')))

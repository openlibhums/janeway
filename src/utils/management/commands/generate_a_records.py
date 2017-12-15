from django.core.management.base import BaseCommand

from django.contrib.sites import models as site_models


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
        sites = site_models.Site.objects.all()

        for site in sites:
            print('{domain}. IN A {ipaddress}'.format(domain=site.domain, ipaddress=options.get('serverip')))

from django.core.management.base import BaseCommand

from journal import models
from core import models as core_models


class Command(BaseCommand):
    """Switches galley files default XSLT to the provided file."""

    help = "Switches galley files XSLT to the provided " \
           "file. Provide 'all' as --journal_code to apply to all journals."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--journal_code')
        parser.add_argument('--xslt_file_id')

    def handle(self, *args, **options):
        """
        Switches a journal or journals default XSLT to the provided file.
        """
        journal_code = options.get('journal_code')
        journals = models.Journal.objects.all()

        if journal_code != 'all':
            journals = journals.filter(code=journal_code)

        xslt_file = core_models.XSLFile.objects.get(
            pk=options.get('xslt_file_id')
        )

        for journal in journals:
            print(f"[Setting XSLT for {journal.name} galleys.]")
            core_models.Galley.objects.filter(
                article__journal=journal,
            ).update(
                xsl_file=xslt_file,
            )
        print('[Complete]')


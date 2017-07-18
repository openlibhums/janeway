from django.core.management.base import BaseCommand

import csv
from utils.importers import shared


class Command(BaseCommand):
    """Takes a Ubiquity Press journal and pulls in the PDF links to patch up similarity check data."""

    help = "Takes a Ubiquity Press journal and pulls in the PDF links to patch up similarity check data."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('input_file')
        parser.add_argument('output_file')

    def handle(self, *args, **options):
        """Imports a set of DOIs into .

        :param args: None
        :param options: Dictionary containing 'input_file', which should contain a list of DOIs
        :return: None
        """
        dict = csv.DictReader(open(options['input_file'], 'r'))

        with open(options['output_file'], 'w') as out_file:
            out = csv.writer(out_file)

            out.writerow(['DOI', '<item crawler="iParadigms">'])

            for row in dict:
                if 'amazonaws' not in row['URL'] and 'uwp.co.uk' not in row['URL']:
                    page = shared.fetch_page(row['URL'])
                    pdf_url = shared.get_pdf_url(page)
                    out.writerow([row['DOI'], pdf_url])
                    out_file.flush()

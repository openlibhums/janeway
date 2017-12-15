import os
import json
import requests

from django.core.management.base import BaseCommand
from django.utils import timezone, translation
from django.conf import settings

from metrics import models
from identifiers import models as ident_models
from journal import models as journal_models


def process_events(file_path):
    json_file = open(file_path, encoding='utf-8')
    json_data = json.loads(json_file.read())
    for event in json_data['message']['events']:
        obj_id_parts = event['obj_id'].split('/')
        doi = '{0}/{1}'.format(obj_id_parts[3], obj_id_parts[4])

        try:
            identifier = ident_models.Identifier.objects.get(id_type='doi', identifier=doi)
            print('{0} found.'.format(doi))
            print(event['subj']['pid'])

            models.AltMetric.objects.get_or_create(
                article=identifier.article,
                source=event['source_id'],
                pid=event['subj']['pid'],
                timestamp=event['timestamp'],
            )
        except ident_models.Identifier.DoesNotExist:
            # This doi isn't found
            pass  # print('{0} not found.'.format(doi))


def fetch_crossref_data(file_path):

    text = ''

    for journal in journal_models.Journal.objects.all():
        if journal.use_crossref:
            try:
                crossref_prefix = journal.get_setting('Identifiers', 'crossref_prefix')
                if crossref_prefix:
                    r = requests.get('https://query.eventdata.crossref.org/events?rows=10000&filter=obj-id.prefix:{0}'.format(crossref_prefix))

                    text = text + r.text
            except IndexError:
                print('{0} has no DOI Prefix set.'.format(journal))
        else:
            print('{0} has not enabled use of Crossref DOIs.'.format(journal))

    json_file = open(file_path, encoding='utf-8')
    json_file.write(text)
    json_file.close()


class Command(BaseCommand):
    """
    A management command that will search for events for each DOI prefix and store them locally before processing them
    """

    help = "Import Crossref Events into local models."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--dump_data', action='store_true', default=False)

    def handle(self, *args, **options):
        """Collects Crossref Events, parses them and stores new events locally.

        :param args: None
        :param options: None
        :return: None
        """

        translation.activate(settings.LANGUAGE_CODE)

        file_name = '{date}.json'.format(date=timezone.localdate())
        file_path = os.path.join(settings.BASE_DIR, 'files', 'temp', file_name)

        if os.path.isfile(file_path):

            # Process file
            print('Existing file found.')
            process_events(file_path)

        else:

            # Fetch data
            print('Fetching data from crossref event tracking API.')
            fetch_crossref_data(file_path)
            # process_events(file_path)

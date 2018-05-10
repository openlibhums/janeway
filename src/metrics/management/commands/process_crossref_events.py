import os
import json
import requests

from django.core.management.base import BaseCommand
from django.utils import timezone, translation
from django.conf import settings
from django.db.utils import IntegrityError

from metrics import models
from identifiers import models as ident_models
from journal import models as journal_models


def process_events():

    for journal in journal_models.Journal.objects.all():
        if journal.use_crossref:
            crossref_prefix = journal.get_setting('Identifiers', 'crossref_prefix')

            file_path = os.path.join(settings.BASE_DIR, 'files', 'temp', '{prefix}.json'.format(prefix=crossref_prefix))
            json_file = open(file_path, encoding='utf-8')
            json_data = json.loads(json_file.read())
            for event in json_data['message']['events']:
                obj_id_parts = event['obj_id'].split('/')
                doi = '{0}/{1}'.format(obj_id_parts[3], obj_id_parts[4])

                try:
                    identifier = ident_models.Identifier.objects.get(id_type='doi', identifier=doi)
                    print('{0} found.'.format(doi))
                    print(event['subj']['pid'])

                    try:
                        models.AltMetric.objects.get_or_create(
                            article=identifier.article,
                            source=event['source_id'],
                            pid=event['subj']['pid'],
                            timestamp=event['timestamp'],
                        )
                    except IntegrityError:
                        print('Duplicate found, skipping.')
                except ident_models.Identifier.DoesNotExist:
                    # This doi isn't found
                    pass  # print('{0} not found.'.format(doi))


def fetch_crossref_data():
    journal_prefixes = list()
    temp_folder = os.path.join(settings.BASE_DIR, 'files', 'temp')

    for journal in journal_models.Journal.objects.all():
        if journal.use_crossref:
            try:
                crossref_prefix = journal.get_setting('Identifiers', 'crossref_prefix')
                journal_prefixes.append(crossref_prefix)
            except IndexError:
                print('{0} has no DOI Prefix set.'.format(journal))

    journal_prefixes = set(journal_prefixes)

    for prefix in journal_prefixes:
        file_path = os.path.join(temp_folder, '{prefix}.json'.format(prefix=prefix))

        if not os.path.isfile(file_path):
            r = requests.get(
                'https://query.eventdata.crossref.org/events?rows=10000&filter=obj-id.prefix:{0}'.format(prefix))

            with open(file_path, 'w') as file:
                file.write(json.dumps(r.json()))


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
            process_events()

        else:

            # Fetch data
            print('Fetching data from crossref event tracking API.')
            fetch_crossref_data()
            process_events()

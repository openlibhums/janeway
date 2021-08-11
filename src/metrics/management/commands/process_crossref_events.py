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

CROSSREF_TEMP_DIR = os.path.join(settings.BASE_DIR, 'files', 'temp', 'crossref')


def process_events(journal_prefixes):

    for prefix in journal_prefixes:
        file_path = os.path.join(
            CROSSREF_TEMP_DIR,
            '{prefix}-{date}.json'.format(
                prefix=prefix,
                date=timezone.localdate(),
            )
        )
        json_file = open(file_path, encoding='utf-8')
        lines = json_file.readlines()
        for line in lines:
            if line:
                json_data = json.loads(line)
                for event in json_data['message']['events']:
                    obj_id_parts = event['obj_id'].split('/')
                    doi = '{0}/{1}'.format(obj_id_parts[3], obj_id_parts[4])

                    try:
                        identifier = ident_models.Identifier.objects.get(id_type='doi', identifier=doi)
                        print('{0} found.'.format(doi))

                        if event.get('action'):
                            print('ACTION:', event['action'])
                        subject = event.get('subj')
                        if subject:
                            pid = subject.get('pid')
                        if subject and pid:
                            obj, c = models.AltMetric.objects.get_or_create(
                                article=identifier.article,
                                source=event['source_id'],
                                pid=event['subj']['pid'],
                                defaults={
                                    'timestamp': event['timestamp']
                                }
                            )
                            if c:
                                print("ALM created {}".format(event['subj']['pid']))
                            else:
                                print("Duplicate {}".format(event['subj']['pid']))
                    except (ident_models.Identifier.DoesNotExist, ident_models.Identifier.MultipleObjectsReturned):
                        # This doi isn't found
                        pass  # print('{0} not found.'.format(doi))


def setup_prefixes(journals):
    journal_prefixes = list()
    for journal in journals:
        if journal.use_crossref:
            try:
                crossref_prefix = journal.get_setting('Identifiers', 'crossref_prefix')
                journal_prefixes.append(crossref_prefix)
            except IndexError:
                print('{0} has no DOI Prefix set.'.format(journal))

    return set(journal_prefixes)


def request_crossref_data(prefix, cursor):
    if cursor:
        response = requests.get(
            'https://api.eventdata.crossref.org/v1/events?mailto=andy.byers@openlibhums.org&obj-id.prefix={}&cursor={}'.format(prefix, cursor)
        )
    else:
        response = requests.get(
            'https://api.eventdata.crossref.org/v1/events?mailto=andy.byers@openlibhums.org&obj-id.prefix={}'.format(prefix)
        )
    return response


def fetch_crossref_data(prefix, cursor=None):

    file_path = os.path.join(
        CROSSREF_TEMP_DIR, '{prefix}-{date}.json'.format(
            prefix=prefix,
            date=timezone.localdate(),
        )
    )

    if not os.path.isfile(file_path):
        responses = []
        cursor = None

        while True:
            response = request_crossref_data(prefix, cursor)
            responses.append(response.json())
            _dict = response.json()
            cursor = _dict['message'].get('next-cursor', None)

            if not cursor:
                break

        for r in responses:
            with open(file_path, 'a') as file:
                file.write('{}\n'.format(json.dumps(r)))


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
        journals = journal_models.Journal.objects.all()
        journal_prefixes = setup_prefixes(journals)

        if not os.path.exists(CROSSREF_TEMP_DIR):
            os.makedirs(CROSSREF_TEMP_DIR)

        for prefix in journal_prefixes:
            file_name = '{prefix}-{date}.json'.format(
                prefix=prefix,
                date=timezone.localdate(),
            )
            file_path = os.path.join(CROSSREF_TEMP_DIR, file_name)

            if os.path.isfile(file_path):
                # Process file
                print('Existing file found.')
                process_events(journal_prefixes)

            else:
                # Fetch data
                print('Fetching data from crossref event tracking API.')
                fetch_crossref_data(prefix)
                process_events(journal_prefixes)

import requests
from pprint import pprint

from django.core.management.base import BaseCommand
from django.conf import settings

from utils import models


def get_logs(message_id):
    return requests.get(
        "https://api.mailgun.net/v3/{0}/events".format(settings.MAILGUN_SERVER_NAME),
        auth=("api", settings.MAILGUN_ACCESS_KEY),
        params={"message-id": message_id})


def check_for_perm_failure(event_dict, log):

    for event in event_dict.get('items'):
        severity = event.get('severity', None)
        if severity == 'permanent':
            return True

    return False


class Command(BaseCommand):
    """Attempts to update mailgun status for log entries"""

    help = "Attempts to update delivery status for mailgun emails."

    def handle(self, *args, **options):

        email_logs = models.LogEntry.objects.filter(is_email=True,
                                                    message_id__isnull=False,
                                                    status_checks_complete=False)

        for log in email_logs:
            logs = get_logs(log.message_id.replace('<', '').replace('>', ''))
            event_dict = logs.json()
            print('Processing ', log.message_id, '...', end='')

            events = []
            for event in event_dict.get('items'):
                events.append(event['event'])

            if 'delivered' in events:
                log.message_status = 'delivered'
                log.status_checks_complete = True
            elif 'failed' in events:
                if check_for_perm_failure(event_dict, log):
                    log.message_status = 'failed'
                    log.status_checks_complete = True
                else:
                    log.message_status = 'accepted'

            elif 'accepted' in events:
                log.message_status = 'accepted'

            log.number_status_checks += 1

            print(' status {0}'.format(log.message_status))

            log.save()

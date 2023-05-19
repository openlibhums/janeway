import requests
from pprint import pprint

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.conf import settings

from utils import models
from submission import models as submission_models


def get_logs(message_id):
    # try to grab the api url from settings otherwise use the default
    try:
        api_url = settings.MAILGUN_API_URL
    except AttributeError:
        api_url = 'https://api.mailgun.net/v3/'

    return requests.get(
        f"{api_url}{settings.MAILGUN_SERVER_NAME}/events",
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

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--article-id', type=int)
        parser.add_argument('--email-log-id', type=int)

    def handle(self, *args, **options):

        if settings.ENABLE_ENHANCED_MAILGUN_FEATURES:
            article_id = options.get('article_id')
            email_log_id = options.get('email_log_id')

            email_logs = models.LogEntry.objects.filter(
                    is_email=True,
                    message_id__isnull=False,
                    status_checks_complete=False,
            )
            if article_id:
                article = submission_models.Article.objects.get(pk=article_id)
                content_type = ContentType.objects.get_for_model(article)
                email_logs = email_logs.filter(
                        content_type=content_type,
                        object_id=article.pk,
                )
            if email_log_id:
                email_logs.filter(pk=email_log_id)

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
        else:
            print('ENHANCED_MAILGUN_FEATURES is set to FALSE in settings.py')

from django.contrib.auth.models import ContentType
from django.core.management.base import BaseCommand
from django.conf import settings

import time
import json
from more_itertools import chunked

from journal import models as journal_models
from repository import models as repository_models
from press import models as press_models
from utils import models as utils_models, setting_handler
from utils.notify_helpers import send_email_with_body_from_user
from utils.logger import get_logger
from cron.models import Request

logger = get_logger(__name__)


class Command(BaseCommand):
    """Sends an email

    Example usage:

    python src/manage.py send_email \
        --journal olhj \
        --to someone@example.org someoneelse@example.org \
        --cc onemore@example.org \
        --bcc bcc.json \
        --subject "Hello" \
        --body my_email.html

    There is currently no support for attachments
    """

    help = 'Sends an email with data passed at command line'

    def add_arguments(self, parser):
        parser.add_argument(
            '--journal',
            help='Journal code',
        )
        parser.add_argument(
            '--repository',
            help='Repository short name',
        )
        parser.add_argument(
            '--to',
            required=True,
            nargs='+',
            help='Email addresses of TO recipients',
        )
        parser.add_argument(
            '--cc',
            nargs='+',
            help='Email addresses of CC recipients',
        )
        parser.add_argument(
            '--bcc',
            help='Filepath to JSON file containing a list of email '
                 'addresses of BCC recipients',
        )
        parser.add_argument(
            '--replyto',
            help='Email address for replies',
        )
        parser.add_argument(
            '--subject',
            required=True,
            help='Subject line'
        )
        parser.add_argument(
            '--body',
            required=True,
            help='Filepath to UTF-8 text file, with optional HTML markup',
        )
        parser.add_argument(
            '--immediately',
            help='By default, you get email data in stdout and must confirm to send. '
                 'Pass --immediately to send immediately',
            action='store_true',
        )
        parser.add_argument(
            '--batchsize',
            help='Batch size for many BCC recipients',
            type=int,
            default=50,
        )

    def handle(self, *args, **options):

        verbosity = options.get('verbosity', 1)

        journal_code = options.get('journal')
        if journal_code:
            try:
                journal = journal_models.Journal.objects.get(
                    code=journal_code
                )
            except journal_models.Journal.DoesNotExist:
                logger.error(
                    self.style.ERROR(
                        f'Journal code not recognised: {journal_code}'
                    )
                )
                if verbosity >= 1:
                    self.print_help('manage.py', 'send_email')
                return
        else:
            journal = None

        repository_short_name = options.get('repository')
        if repository_short_name:
            try:
                repository= repository_models.Repository.objects.get(
                    short_name=repository_short_name
                )
            except repository_models.Repository.DoesNotExist:
                logger.error(
                    self.style.ERROR(
                        f'Repository short name not recognised: '
                        f'{repository_short_name}'
                    )
                )
                if verbosity >= 1:
                    self.print_help('manage.py', 'send_email')
                return
        else:
            repository = None

        press = press_models.Press.objects.first()

        request = Request()
        request.META = {}
        request.journal = journal
        request.press = press
        request.repository = None
        if journal:
            request.site_type = journal
        elif repository:
            request.site_type = repository
        else:
            request.site_type = press

        subject = options['subject']
        to = options['to']

        body_file = options['body']
        try:
            with open(body_file, 'r') as ref:
                body = ref.read()
        except FileNotFoundError:
            logger.error(self.style.ERROR(f'File not found at {body_file}'))
            if verbosity >= 1:
                self.print_help('manage.py', 'send_email')
            return

        log_subject = f'"{subject}" sent from {request.site_type} ' \
                      'with Django management command.'
        log_dict = {
            'level': 'Info',
            'action_text': log_subject,
            'types': 'Email',
            'target': None,
        }
        cc = options.get('cc') or ''

        batch_size = options['batchsize']

        if (len(to) + len(cc)) > batch_size:
            logger.error(
                self.style.ERROR(
                    f'TO and CC must have fewer than {batch_size} addresses'
                )
            )
            return

        if not options['bcc']:
            bcc = []
        else:
            bcc_file = options['bcc']
            try:
                with open(bcc_file, 'r') as ref:
                    bcc = json.loads(ref.read())
            except FileNotFoundError:
                logger.error(
                    self.style.ERROR(f'File not found at {bcc_file}')
                )
                if verbosity >= 1:
                    self.print_help('manage.py', 'send_email')
                return

        if len(bcc) > batch_size:

            batch_num = 1
            log_dict['action_text'] = f'{log_subject} (batch {batch_num})'

            if options['replyto']:
                reply_to = (options['replyto'],)
            else:
                custom_reply_to_setting = setting_handler.get_setting(
                    'general',
                    'replyto_address',
                    journal,
                )
                if custom_reply_to_setting and custom_reply_to_setting.value:
                    reply_to = (custom_reply_to_setting.value,)
                else:
                    logger.error(
                        self.style.ERROR(
                            f'--replyto argument or '
                            f'replyto_address setting value needed for BCC list '
                            f'length over {batch_size}'
                        )
                    )
                    return

        if not options['immediately']:
            logger.info(
                f'\n\n'
                f'Preparing to send email from {request.site_type}\n\n'
                f'Subject: {subject}\n\n'
                f'TO: {to}\n\n'
                f'CC: {cc}\n\n'
                f'BCC: {bcc}\n\n'
                f'Body: \n{body}\n\n'
            )

            send = input('Send? (yes/no): ')

            if not send.lower() == 'yes':
                logger.info('Email discarded')
                return

        # Send batch 1
        bcc_chunk = bcc[:batch_size]
        send_email_with_body_from_user(
            request,
            subject,
            to,
            body,
            log_dict=log_dict,
            cc=cc,
            bcc=bcc_chunk,
        )

        # Send the rest with noreply address in TO and empty CC
        if len(bcc) > batch_size:
            to = reply_to
            cc = []
            for i, bcc_chunk in enumerate(
                chunked(bcc[batch_size:], batch_size)
            ):
                time.sleep(0.5)
                batch_num = i + 2
                log_dict['action_text'] = f'{log_subject} (batch {batch_num})'
                send_email_with_body_from_user(
                    request,
                    subject,
                    to,
                    body,
                    log_dict=log_dict,
                    cc=cc,
                    bcc=bcc_chunk,
                )

        logger.info(self.style.SUCCESS('Email sent'))

        new_log = utils_models.LogEntry.objects.filter(
            subject__contains=log_subject
        ).last()
        if new_log:
            logger.info(f'Log: {new_log}')
        else:
            logger.warn(
                self.style.WARNING(
                    'Email not logged. You may want to '
                    'double-check it was sent.'
                )
            )

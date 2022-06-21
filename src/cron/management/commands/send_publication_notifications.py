from mock import Mock

from django.shortcuts import reverse
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.http import HttpRequest

from journal import models as journal_models
from submission import models as submission_models
from utils import notify_helpers, setting_handler, render_template


def create_fake_request(journal):
    request = Mock(HttpRequest)
    request.GET = Mock()
    request.journal = journal
    request.user = None
    request.site_type = journal
    request.FILES = None
    request.META = {}

    return request


class Command(BaseCommand):
    """A management command that sends article/issue publication notifications."""

    help = "Sends out article/issue publication notifications to users in the reader role.."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code', nargs='?', default=None)

    def handle(self, *args, **options):
        journal_code = options.get('journal_code', None)
        journals = journal_models.Journal.objects.all()
        if journal_code:
            journals = journals.filter(code=journal_code)

        for journal in journals:
            if setting_handler.get_setting(
                setting_group_name='notification',
                setting_name='send_reader_publication_notifications',
                journal=journal,
            ).value:
                print('Sending notification for {}'.format(journal.name))
                readers = journal.users_with_role('reader')
                bcc_list = [reader.email for reader in readers]

                if bcc_list:
                    print("Sending notifications to {}".format(
                        ", ".join(bcc_list)
                    ))

                today = timezone.now().today().date()
                start = timezone.now().replace(hour=0, minute=0, second=0)
                end = timezone.now().replace(hour=23, minute=59, second=59)
                articles_published_today = submission_models.Article.objects.filter(
                    date_published__gte=start,
                    date_published__lte=end,
                    journal=journal,
                    stage=submission_models.STAGE_PUBLISHED,
                )
                if articles_published_today.exists():
                    context = {
                        'articles': articles_published_today,
                        'journal': journal,
                    }

                    html = render_template.get_requestless_content(
                        context=context,
                        journal=journal,
                        template='reader_publication_notification',
                    )
                    html = html + "<p>You can unsubscribe from publication notifications on your profile page: {}</p>".format(
                        journal.site_url(
                            reverse(
                                'core_edit_profile',
                            )
                        )
                    )

                    notify_helpers.send_email_with_body_from_user(
                        request=create_fake_request(journal),
                        subject=setting_handler.get_setting('email_subject', 'subject_reader_publication_notification', journal).value,
                        to=setting_handler.get_setting('general', 'from_address', journal).value,
                        body=html,
                        bcc=bcc_list,
                        log_dict={
                            'level': 'Info',
                            'action_text': 'Publication notification sent',
                            'types': 'Publication Notification',
                            'target': journal,
                        }
                    )
                else:
                    print("No articles were published today.")
            else:
                print('Reader publication notifications are not enabled for {}'.format(journal.name))



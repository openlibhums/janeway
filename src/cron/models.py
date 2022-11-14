__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.db import models
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from django.shortcuts import reverse

from cron import logic
from journal import models as journal_models
from utils import render_template, notify_helpers
from submission import models as submission_models
from review import logic as review_logic
from utils.logger import get_logger

logger = get_logger(__name__)


class CronTask(models.Model):
    task_type = models.CharField(max_length=255)
    task_data = models.TextField(blank=True, null=True)
    added = models.DateTimeField(default=timezone.now)
    run_at = models.DateTimeField(default=timezone.now)
    article = models.ForeignKey('submission.Article', blank=True, null=True)

    email_to = models.EmailField(blank=True, null=True)
    email_subject = models.CharField(max_length=255, blank=True, null=True)
    email_journal = models.ForeignKey(journal_models.Journal, blank=True, null=True)
    email_html = models.TextField(blank=True, null=True)
    email_cc = models.CharField(max_length=255, blank=True, null=True)
    email_bcc = models.CharField(max_length=255, blank=True, null=True)

    @staticmethod
    def run_tasks():
        tasks = CronTask.objects.filter(run_at__lt=timezone.now())

        if tasks.exists():
            # run five cron items
            for task in tasks[0:5]:
                logic.task_runner(task)

                task.delete()

    @staticmethod
    def add_email_task(to, subject, html, request, article=None, run_at=timezone.now(), cc=None, bcc=None):
        task = CronTask()

        task.task_type = 'email_message'
        task.run_at = run_at

        task.email_to = to
        task.email_subject = subject
        task.email_html = html
        task.email_journal = request.journal
        task.cc = cc
        task.bcc = bcc
        task.article = article

        task.save()


REMINDER_CHOICES = (
    ('review', 'Review (Invited)'),
    ('accepted-review', 'Review (Accepted)'),
    ('revisions', 'Revision'),
)

RUN_TYPE_CHOICES = (
    # Before the event
    ('before', 'Before'),
    # After the event
    ('after', 'After'),
)


class SentReminder(models.Model):
    type = models.CharField(max_length=100, choices=REMINDER_CHOICES)
    object_id = models.PositiveIntegerField()
    sent = models.DateField(default=timezone.now)


class Reminder(models.Model):
    journal = models.ForeignKey('journal.Journal')
    type = models.CharField(max_length=100, choices=REMINDER_CHOICES)
    run_type = models.CharField(max_length=100, choices=RUN_TYPE_CHOICES)
    days = models.PositiveIntegerField(help_text="The number of days before or after this reminder should fire")
    template_name = models.CharField(max_length=100, help_text="The name of the email template, if it doesn't exist "
                                                               "you will be asked to create it. Should have no spaces.")
    subject = models.CharField(max_length=200)

    def __str__(self):
        return "{0}: {1}, {2}, {3}".format(self.journal.code, self.run_type, self.type, self.subject)

    def target_date(self):
        """
        Works out the target date of a reminder by adding or subtracting a timedelta from today's date.
        Examples: Reminder set to send 5 days before the due date we take today's date and add 5 days to search
        for ReviewAssignments that are due 5 days from now. The reverse is true for after, we remove 5 days from
        today's date to work out which ReviewAssignments were due 5 days ago.
        """
        date_time = None

        if self.run_type == 'before':
            date_time = timezone.now() + timedelta(days=self.days)
        elif self.run_type == 'after':
            date_time = timezone.now() - timedelta(days=self.days)

        if date_time:
            return date_time
        else:
            return None

    def items_for_reminder(self):
        model, objects, query = None, None, None
        from review import models as review_models

        if self.type == 'review':
            model = review_models.ReviewAssignment
            query = (Q(date_declined__isnull=True) &
                     Q(date_complete__isnull=True) &
                     Q(date_accepted__isnull=True) &
                     Q(article__stage__in=submission_models.REVIEW_STAGES))
        elif self.type == 'accepted-review':
            model = review_models.ReviewAssignment
            query = (Q(date_declined__isnull=True) &
                     Q(date_complete__isnull=True) &
                     Q(date_accepted__isnull=False) &
                     Q(article__stage__in=submission_models.REVIEW_STAGES))
        elif self.type == 'revisions':
            model = review_models.RevisionRequest
            query = (Q(date_completed__isnull=True) &
                     Q(article__stage__in=submission_models.REVIEW_STAGES))

        target_date = self.target_date()
        if target_date:
            objects = model.objects.filter(date_due=target_date).filter(query, article__journal=self.journal)

        return objects

    def send_reminder(self, test=False):
        from review import models as review_models
        objects = self.items_for_reminder()
        request = Request()
        request.journal = self.journal
        request.site_type = self.journal
        to = None

        for item in objects:
            sent_check = SentReminder.objects.filter(
                type=self.type,
                object_id=item.pk,
                sent=timezone.now().date(),
            )

            # Create context early so qw can add the correct variable
            context = {'journal': self.journal, 'article': item.article}
            # Check if the item is a ReviewAssignment or RevisionRequest
            if isinstance(item, review_models.ReviewAssignment):
                to = item.reviewer.email
                context['review_assignment'] = item

                # get the review_url for the email context
                review_url = review_logic.get_review_url(request, item)
                context['review_url'] = review_url

            elif isinstance(item, review_models.RevisionRequest):
                to = item.article.correspondence_author.email
                context['revision'] = item

                # get the do_revisions url
                do_revisions_url = request.journal.site_url(path=reverse(
                    'do_revisions',
                    kwargs={
                        'article_id': item.article.pk,
                        'revision_id': item.pk,
                    }
                ))
                context['do_revisions_url'] = do_revisions_url

            if not test and not sent_check and to:
                message = render_template.get_requestless_content(
                    context,
                    self.journal,
                    self.template_name,
                )

                notify_helpers.send_email_with_body_from_user(
                    request,
                    self.subject,
                    to,
                    message,
                )
                # Create a SentReminder object to ensure we don't do this more than once by accident.
                SentReminder.objects.create(type=self.type, object_id=item.pk)
                logger.info('Reminder sent for {0}'.format(item))
            elif test:
                logger.info("[TEST] reminder for {} due on {}".format(item, item.date_due))
            else:
                logger.info('Reminder {0} for object {1} has already been sent'.format(self, item))


class Request(object):
    """
    A fake request class for sending emails outside of the client-server request loop.
    """

    def __init__(self):
        self.journal = None
        self.site_type = None
        self.port = 8000
        self.secure = False
        self.user = False
        self.FILES = None

    def is_secure(self):
        if self.secure is False:
            return False
        else:
            return True

from datetime import date

from django.db import models
from django.utils import timezone

from utils import notify_helpers


def review_choices():
    return (
        ('accept', 'Accept'),
        ('corrections', 'Corrections Required'),
        ('proofing', 'Proofing Required'),
    )


class TypesettingClaim(models.Model):
    editor = models.ForeignKey('core.Account')
    article = models.OneToOneField('submission.Article')
    claimed = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('editor', 'article',)


class TypesettingRound(models.Model):
    article = models.ForeignKey('submission.Article')
    round_number = models.PositiveIntegerField(default=1)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-round_number',)

    def __str__(self):
        return str(self.round_number)


class TypesettingAssignment(models.Model):
    round = models.OneToOneField(TypesettingRound)
    manager = models.ForeignKey(
        'core.Account',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='manager',
    )
    typesetter = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
        related_name='typesetter',
    )

    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    accepted = models.DateTimeField(blank=True, null=True)
    due = models.DateField(null=True)
    completed = models.DateTimeField(blank=True, null=True)
    reviewed = models.BooleanField(default=False)
    review_decision = models.CharField(
        choices=review_choices(),
        max_length=21,
    )

    task = models.TextField(
        null=True,
        verbose_name='Typesetting Task',
    )
    files_to_typeset = models.ManyToManyField(
        'core.File',
        related_name='files_to_typeset',
        blank=True,
    )
    galleys_created = models.ManyToManyField(
        'core.Galley',
        blank=True,
    )
    typesetter_note = models.TextField(
        blank=True,
        verbose_name='Note to Editor',
    )

    @property
    def is_active(self):
        if self.assigned and not self.completed:
            return True
        else:
            return False

    @property
    def status(self):
        if self.assigned and not self.accepted and not self.completed:
            return "assigned"
        elif self.assigned and self.accepted and not self.completed:
            return "accepted"
        elif self.assigned and not self.accepted and self.completed:
            return "declined"
        elif self.completed and not self.reviewed:
            return "completed"
        elif self.completed and self.reviewed:
            return self.get_review_decision_display()
        else:
            return "unknown"

    @property
    def is_overdue(self):
        if self.due and self.due < date.today():
            return True
        return False

    FRIENDLY_STATUSES = {
        "assigned": "Awaiting response",
        "accepted": "Task accepted",
        "declined": "Task declined",
        "completed": "Task completed",
        "closed": "Task closed",
        "unknown": "Task status unknown",
    }

    @property
    def friendly_status(self):
        return self.FRIENDLY_STATUSES.get(self.status)

    def send_notification(self, message, request, skip=False):
        description = '{0} has been assigned as a typesetter for {1}'.format(
            self.typesetter.full_name(),
            self.round.article.title,
        )

        if not skip:
            log_dict = {
                'level': 'Info',
                'action_text': description,
                'types': 'Typesetting Assignment',
                'target': self.round.article,
            }
            notify_helpers.send_email_with_body_from_user(
                request,
                'subject_typesetter_notification',
                self.typesetter.email,
                message,
                log_dict=log_dict,
            )
            notify_helpers.send_slack(
                request,
                description,
                ['slack_editors'],
            )

            self.notified = True
            self.save()





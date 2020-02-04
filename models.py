from datetime import date

from django.db import models
from django.utils import timezone


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


class TypesettingAssignment(models.Model):
    round = models.ForeignKey(TypesettingRound)
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





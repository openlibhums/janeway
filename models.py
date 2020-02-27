from datetime import date

from django.db import models
from django.utils import timezone

from utils import models as utils_models
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
        ordering = ('-round_number', 'date_created')
        unique_together = ('round_number', 'article',)

    def __str__(self):
        return str(self.round_number)


    @property
    def has_open_tasks(self):
        if hasattr(self, 'typesettingassignment'):
            if not self.typesettingassignment.done:
                return True

        #TODO: Check proofing tasks as well
        return False


    def close(self, user=None):
        """ Method that closes a round by cancelling any open tasks """
        if hasattr(self, 'typesettingassignment'):
            if self.typesettingassignment.is_active:
                self.typesettingassignment.delete(user=user)

        #TODO: Cancel proofing tasks


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
        blank=True,
    )

    task = models.TextField(
        null=True,
        verbose_name='Typesetting Task',
        help_text='Please let the typesetter know what you want them to create'
                  ' and if there are any special circumstances. They will have'
                  ' access to the articles metadata.',
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
    def time_to_due(self):
        return self.due - timezone.now().date()

    @property
    def is_active(self):
        return self.assigned and not self.completed

    @property
    def status(self):
        if self.assigned and not self.accepted and not self.completed:
            return "assigned"
        elif self.assigned and self.accepted and not self.completed:
            return "accepted"
        elif self.declined:
            return "declined"
        elif self.done and not self.reviewed:
            return "completed"
        elif self.done and self.reviewed:
            return self.get_review_decision_display()
        else:
            return "unknown"

    @property
    def done(self):
        return self.completed and self.accepted

    @property
    def declined(self):
        return self.completed and not self.accepted

    @property
    def is_overdue(self):
        return self.due and self.due < date.today()

    def reopen(self, user):
        self.completed = self.acccepted = None
        self.notified = False
        utils_models.LogEntry.add_entry(
            types="Typesetting reopened",
            description="The typesetting assignment {self.pk} has been "
            "re-opened by user {user}".format(self=self, user=user),
            level="INFO",
            actor=user,
            target=self.round.article,
        )
        self.save()

    def delete(self, user=None):
        utils_models.LogEntry.add_entry(
            types="Typesetting deleted",
            description="The typesetting assignment {self.pk} has been "
            "deleted by user {user}".format(self=self, user=user),
            level="INFO",
            actor=user,
            target=self.round.article,
        )
        super().delete()

    FRIENDLY_STATUSES = {
        "assigned": "Awaiting response from the typesetter.",
        "accepted": "Typesetter has accepted task, awaiting completion.",
        "declined": "Typesetter has declined this task.",
        "completed": "The typesetter has completed their task. "
                     "You should review the uploaded galley files.",
        "closed": "Task closed",
        "unknown": "Task status unknown",
        "Corrections Required": "This article requires corrections.",
        "Proofing Required": "This article requires proofing.",
        "Accept": "Typesetting for this article has been accepted."
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

    def send_decision_notification(self, request, note, decision):
        description = 'Typesetting task {0} decision made by {1}: {2}'.format(
            self.pk,
            self.typesetter.full_name(),
            decision,
        )

        log_dict = {
            'level': 'Info',
            'action_text': description,
            'types': 'Typesetting Assignment Decision',
            'target': self.round.article,
        }

        notify_helpers.send_email_with_body_from_setting_template(
            request,
            'typsetting_typesetter_decision_{}'.format(decision),
            'Typesetting Assignment Decision',
            self.manager.email,
            context={'assignment': self, 'note': note},
            log_dict=log_dict,
        )

    def complete(self, note, galleys):
        self.typesetter_note = note

        for galley in galleys:
            self.galleys_created.add(galley)

        self.completed = timezone.now()
        self.save()

    def send_complete_notification(self, request):
        description = 'Typesetting task completed by {0}'.format(
            self.typesetter.full_name(),
        )

        log_dict = {
            'level': 'Info',
            'action_text': description,
            'types': 'Typesetting Complete',
            'target': self.round.article,
        }

        notify_helpers.send_email_with_body_from_setting_template(
            request,
            'typesetting_typesetter_complete',
            'Typesetting Assignment Complete',
            self.manager.email,
            context={'assignment': self},
            log_dict=log_dict,
        )


class GalleyProofing(models.Model):
    round = models.ForeignKey(TypesettingRound)
    manager = models.ForeignKey('core.Account', related_name='galley_manager')
    proofreader = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,

    )
    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    due = models.DateTimeField(default=None, verbose_name="Date Due")
    accepted = models.DateTimeField(blank=True, null=True)
    completed = models.DateTimeField(blank=True, null=True)
    cancelled = models.BooleanField(default=False)

    task = models.TextField(
        verbose_name="Proofing Task",
        help_text='If there is any additional information or direction you '
                  'can give the proofreader to complete their task you can '
                  'add it here.',
    )
    proofed_files = models.ManyToManyField('core.Galley')
    notes = models.TextField()
    annotated_files = models.ManyToManyField('core.File')

    def __str__(self):
        return 'Proofing for Article {0} by {1}'.format(
            self.round.article.title,
            self.proofreader.full_name(),
        )

    def send_assignment_notification(self, request, message, skip=False):
        description = '{0} has been assigned as a proofreader for {1}'.format(
            self.proofreader.full_name(),
            self.round.article.title,
        )

        if not skip:
            log_dict = {
                'level': 'Info',
                'action_text': description,
                'types': 'Proofing Assignment',
                'target': self.round.article,
            }
            notify_helpers.send_email_with_body_from_user(
                request,
                'Proofing Request',
                self.proofreader.email,
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


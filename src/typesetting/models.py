from datetime import date, timedelta

from django.db import models
from django.utils import timezone

from core.model_utils import JanewayBleachField
from utils import models as utils_models
from utils import notify_helpers
from submission import models as submission_models


def review_choices():
    return (
        ('accept', 'Accept'),
        ('corrections', 'Corrections Required'),
        ('proofing', 'Proofing Required'),
    )


class TypesettingClaim(models.Model):
    editor = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    article = models.OneToOneField(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    claimed = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('editor', 'article',)


class TypesettingRound(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    round_number = models.PositiveIntegerField(default=1)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-round_number', 'date_created')
        unique_together = ('round_number', 'article',)

    def __str__(self):
        return str(self.round_number)

    @property
    def has_completed_proofing(self):
        return GalleyProofing.objects.filter(
            round=self,
            accepted__isnull=False,
            completed__isnull=False,
        )

    @property
    def has_open_tasks(self):
        if hasattr(self, 'typesettingassignment'):
            if not self.typesettingassignment.done:
                return True

        if self.galleyproofing_set.filter(completed__isnull=True).exists():
            return True

        return False

    def close(self, user=None):
        """ Method that closes a round by cancelling any open tasks """
        if hasattr(self, 'typesettingassignment'):
            if self.typesettingassignment.is_active:
                self.typesettingassignment.cancel(user=user)

        for proofing in self.galleyproofing_set.filter(
            completed__isnull=True,
        ):
            proofing.cancel(user=user)


class ActiveTypesettingAssignmentManager(models.Manager):
    def get_queryset(self):
        return super(ActiveTypesettingAssignmentManager, self).get_queryset().exclude(
            round__article__stage=submission_models.STAGE_ARCHIVED,
        )


class TypesettingAssignment(models.Model):
    round = models.OneToOneField(
        TypesettingRound,
        on_delete=models.CASCADE,
    )
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
    cancelled = models.DateTimeField(blank=True, null=True)
    reviewed = models.BooleanField(default=False)
    display_proof_comments = models.BooleanField(
        default=True,
        help_text="Allow the typesetter to see the proofreading comments",
    )
    review_decision = models.CharField(
        choices=review_choices(),
        max_length=21,
        blank=True,
    )

    task = JanewayBleachField(
        blank=True,
        verbose_name='Typesetting Task',
        help_text='The task description if not explained in the typesetting guidelines.',
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
    typesetter_note = JanewayBleachField(
        blank=True,
        verbose_name='Note to Editor',
    )

    objects = models.Manager()
    active_objects = ActiveTypesettingAssignmentManager()

    @property
    def time_to_due(self):
        if not self.due:
            return ''
        due = self.due - timezone.now().date()
        if due == timedelta(0):
            return 'Due Today'
        elif due < timedelta(0):
            return 'Overdue'

        return '{} days'.format(due.days)

    @property
    def is_active(self):
        return self.assigned and not self.completed

    @property
    def status(self):
        if self.cancelled:
            return "cancelled"
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

    def reopen(self, user=None):
        self.completed = self.accepted = None
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

    def cancel(self, user=None):
        utils_models.LogEntry.add_entry(
            types="Typesetting Task cancelled",
            description="The typesetting assignment {self.pk} has been "
            "cancelled by user {user}".format(self=self, user=user),
            level="INFO",
            actor=user,
            target=self.round.article,
        )
        self.cancelled = timezone.now()
        self.save()

    def complete(self, note='', user=None):
        utils_models.LogEntry.add_entry(
            types="Typesetting Task Completed",
            description="The typesetting assignment {self.pk} has been "
                        "completed by user {user}".format(self=self, user=user),
            level="INFO",
            actor=user,
            target=self.round.article,
        )

        self.typesetter_note = note

        if not self.accepted:
            self.accepted = timezone.now()

        self.completed = timezone.now()
        self.save()

    FRIENDLY_STATUSES = {
        "assigned": "Awaiting response from the typesetter.",
        "accepted": "Typesetter has accepted task, awaiting completion.",
        "declined": "Typesetter has declined this task.",
        "completed": "The typesetter has completed their task. "
                     "You should review the uploaded galley files.",
        "cancelled": "The manager has cancelled this typesetting task",
        "closed": "Task closed",
        "unknown": "Task status unknown",
        "Corrections Required": "This article requires corrections.",
        "Proofing Required": "This article requires proofing.",
        "Accept": "Typesetting for this article has been completed. However,"
            " if you want to make further changes, you can still assign"
            " proofreaders or start a new typesetting round.",
    }

    @property
    def friendly_status(self):
        return self.FRIENDLY_STATUSES.get(self.status)

    def proofing_assignments_for_corrections(self):
        """ Returns the proofreading assignemnts for corrections
        The proofreadings relevant for round n of proofing would have been
        stored against round n-1 of this article
        """
        rounds = TypesettingRound.objects.filter(article=self.round.article)
        if rounds.count() > 1:
            previous_round = rounds[1]
            proofing_assignments = previous_round.galleyproofing_set.filter(
                completed__isnull=False,
                cancelled=False,
            )
            return proofing_assignments
        else:
            return GalleyProofing.objects.none()

    def __str__(self):
        return f'Typesetter {self.typesetter} assigned to article {self.round.article}'


class ActiveGalleyProofingManager(models.Manager):
    def get_queryset(self):
        return super(ActiveGalleyProofingManager, self).get_queryset().exclude(
            round__article__stage=submission_models.STAGE_ARCHIVED
        )


class GalleyProofing(models.Model):
    round = models.ForeignKey(
        TypesettingRound,
        on_delete=models.CASCADE,
    )
    manager = models.ForeignKey(
        'core.Account',
        null=True,
        related_name='galley_manager',
        on_delete=models.SET_NULL,
    )
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

    task = JanewayBleachField(
        verbose_name="Proofing Task",
        help_text='Add any additional information or instructions '
                  'for the proofreader here.',
    )
    proofed_files = models.ManyToManyField('core.Galley', blank=True)
    notes = JanewayBleachField(blank=True)
    annotated_files = models.ManyToManyField('core.File', blank=True)

    objects = models.Manager()
    active_objects = ActiveGalleyProofingManager()

    class Meta:
        ordering = ('assigned', 'accepted', 'pk')

    def __str__(self):
        return 'Proofing for Article {0} by {1}'.format(
            self.round.article.title,
            self.proofreader.full_name() if self.proofreader else '',
        )

    def assign(self, user=None, skip=False):
        if not skip:
            self.notified = True
            self.save()

        utils_models.LogEntry.add_entry(
            types='Proofreader Assigned',
            description='{} assigned as a proofreader by {}'.format(
                self.proofreader.full_name(),
                user,
            ),
            level='Info',
            actor=user,
            target=self.round.article,
        )

    def cancel(self, user=None):
        self.cancelled = True
        self.completed = timezone.now()
        self.save()

        utils_models.LogEntry.add_entry(
            types='Proofreading Assignment Cancelled',
            description='Proofing by {} cancelled by {}'.format(
                self.proofreader.full_name(),
                user,
            ),
            level='Info',
            actor=user,
            target=self.round.article,
        )

    def reset(self, user=None):
        self.cancelled = False
        self.completed = None
        self.accepted = None
        self.save()

        utils_models.LogEntry.add_entry(
            types='Proofreading Assignment Reset',
            description='Proofing by {} reset by {}'.format(
                self.proofreader.full_name(),
                user,
            ),
            level='Info',
            actor=user,
            target=self.round.article,
        )

    def complete(self, user=None):
        self.cancelled = False
        self.completed = timezone.now()
        self.accepted = timezone.now()
        self.save()

        utils_models.LogEntry.add_entry(
            types='Proofreading Assignment Complete',
            description='Proofing by {} completed'.format(
                user,
            ),
            level='Info',
            actor=user,
            target=self.round.article,
        )

    def unproofed_galleys(self, galleys):
        check = []
        proofed_files = self.proofed_files.all()

        for galley in galleys:
            if galley not in proofed_files:
                check.append(galley)

        return check

    @property
    def time_to_due(self):
        due = self.due.date() - timezone.now().date()

        if due == timedelta(0):
            return 'Due Today'
        elif due < timedelta(0):
            return 'Overdue'

        return '{} days'.format(due.days)

    FRIENDLY_STATUSES = {
        "assigned": "Awaiting response from the proofreader.",
        "accepted": "Proofreader has accepted task, awaiting completion.",
        "declined": "Proofreader has declined this task.",
        "completed": "The proofreader has completed their task. "
                     "You should review their response.",
        "unknown": "Task status unknown.",
        "cancelled": "Task was cancelled by manager/editor."
    }

    @property
    def status(self):
        if self.cancelled:
            return 'cancelled'
        elif self.assigned and self.accepted and not self.completed:
            return 'accepted'
        elif self.assigned and self.completed and not self.accepted:
            return 'declined'
        elif self.assigned and self.completed and self.accepted:
            return 'completed'
        elif self.assigned and not self.accepted and not self.completed:
            return 'assigned'
        else:
            return 'unknown'

    @property
    def friendly_status(self):
        return self.FRIENDLY_STATUSES.get(self.status)

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


class TypesettingCorrection(models.Model):
    task = models.ForeignKey(
        "typesetting.TypesettingAssignment",
        related_name="corrections",
        blank=True,
        on_delete=models.CASCADE,
    )
    galley = models.ForeignKey(
        "core.Galley",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # A copy of the galley label, in case the galley is deleted
    label = models.CharField(max_length=255, blank=True, null=True)
    date_requested = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(blank=True, null=True)
    date_declined = models.DateTimeField(blank=True, null=True)
    # A copy of the file checksum to detect changes when requesting corrections
    file_checksum = models.CharField(max_length=255, blank=True, null=True)

    @property
    def status(self):
        _status = "pending"
        if self.date_completed:
            _status = "completed"
        elif self.date_declined:
            _status = "declined"
        return _status

    def save(self, *args, **kwargs):
        if not self.pk and not self.file_checksum:
            self.file_checksum = self.galley.file.checksum()
        super().save(*args, **kwargs)

    @property
    def corrected(self):
        if self.galley:
            return self.file_checksum != self.galley.file.checksum()
        return False

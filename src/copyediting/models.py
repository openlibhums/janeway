__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.db import models
from django.utils import timezone

from submission import models as submission_models


def copyeditor_decisions():
    return (
        ('accept', 'Accept'),
        ('decline', 'Decline'),
        ('cancelled', 'Cancelled'),
    )


def author_decisions():
    return (
        ('accept', 'Accept'),
        ('corrections', 'Corrections Required'),
    )


class ActiveCopyeditAssignmentManager(models.Manager):
    def get_queryset(self):
        return super(ActiveCopyeditAssignmentManager, self).get_queryset().exclude(
            article__stage=submission_models.STAGE_ARCHIVED,
        )


class CopyeditAssignment(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    copyeditor = models.ForeignKey('core.Account', related_name='copyeditor', null=True, on_delete=models.SET_NULL)
    editor = models.ForeignKey('core.Account', related_name='cp_editor', null=True, on_delete=models.SET_NULL)

    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    due = models.DateField(default=timezone.now)

    editor_note = models.TextField(blank=True, null=True, verbose_name='Note for the Copyeditor')
    copyeditor_note = models.TextField(blank=True, null=True, verbose_name='Note for the Editor')

    decision = models.CharField(max_length=20, choices=copyeditor_decisions(), null=True, blank=True)
    date_decided = models.DateTimeField(null=True, blank=True)

    files_for_copyediting = models.ManyToManyField('core.File', related_name='files_for_copyediting')
    copyeditor_files = models.ManyToManyField(
        'core.File',
        blank=True,
        related_name='copyeditor_files',
    )
    copyeditor_completed = models.DateTimeField(blank=True, null=True)

    copyedit_reopened = models.DateTimeField(blank=True, null=True)
    copyedit_reopened_complete = models.DateTimeField(blank=True, null=True, help_text="The date a reopen was complete")
    copyedit_accepted = models.DateTimeField(blank=True, null=True)

    copyedit_acknowledged = models.BooleanField(default=False)

    objects = models.Manager()
    active_objects = ActiveCopyeditAssignmentManager()

    class Meta:
        ordering = ('assigned',)

    def __str__(self):
        return "Assignment of {0} to {1}".format(self.copyeditor.full_name(), self.article)

    def author_reviews(self):
        return AuthorReview.objects.filter(assignment=self).order_by('assigned')

    def active_author_reviews(self):
        return AuthorReview.objects.filter(assignment=self, date_decided__isnull=True)

    def actions_available(self):
        if self.decision == 'accept' and self.copyeditor_completed and not self.copyedit_reopened and not \
                self.copyedit_accepted and not self.incomplete_author_reviews():
            return True
        elif self.decision == 'accept' and self.copyeditor_completed and self.copyedit_reopened_complete and not \
                self.copyedit_accepted and not self.incomplete_author_reviews():
            return True
        else:
            return False

    def incomplete_author_reviews(self):
        check = False

        for review in self.author_reviews():
            if not review.decision:
                check = True
        return check

    def copyedit_log(self):
        log = list()

        log.append({'date': self.assigned, 'event': 'Copyedit request assigned', 'slug': 'assigned'})
        for review in self.author_reviews():
            log.append({'date': review.assigned, 'event': 'Author review requested', 'slug': 'author_review'})
            if review.date_decided:
                log.append({'date': review.date_decided, 'event': 'Author completed review',
                            'slug': 'author_complete'})

        if self.copyeditor_completed:
            log.append({'date': self.copyeditor_completed, 'event': 'Initial copyedit complete', 'slug': 'initial'})
        if self.copyedit_reopened:
            log.append({'date': self.copyedit_reopened, 'event': 'Copyedit reopened', 'slug': 'reopened'})
        if self.date_decided:
            log.append({'date': self.date_decided, 'event': 'Copyeditor request decision: {0}'.format(self.decision),
                        'slug': 'decision'})
        if self.copyedit_reopened_complete:
            log.append({'date': self.copyedit_reopened_complete, 'event': 'Copyeditor completed additional edits',
                        'slug': 'reopened_complete'})
        if self.copyedit_accepted:
            log.append({'date': self.copyedit_accepted, 'event': 'Editor accepted the copyedit', 'slug': 'accepted'})
        return sorted(log, key=lambda k: k['date'])


class ActiveAuthorReviewManager(models.Manager):
    def get_queryset(self):
        return super(ActiveAuthorReviewManager, self).get_queryset().exclude(
            assignment__article__stage=submission_models.STAGE_ARCHIVED,
        )


class AuthorReview(models.Model):
    author = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    assignment = models.ForeignKey(
        CopyeditAssignment,
        on_delete=models.CASCADE,
    )

    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)

    decision = models.CharField(max_length=20, choices=author_decisions(), null=True, blank=True,
                                help_text='Select a decision that reflects your actions. If you\'ve uploaded a new '
                                          'version of the file, select Corrections Required, if you\'re happy with the '
                                          'copyedit, select Accept.',
                                verbose_name='Your Decision')
    date_decided = models.DateTimeField(null=True, blank=True)
    author_note = models.TextField(null=True, blank=True, verbose_name='Note to the Editor')

    files_updated = models.ManyToManyField(
        'core.File',
        verbose_name='files_updated',
        blank=True,
    )

    objects = models.Manager()
    active_objects = ActiveAuthorReviewManager()

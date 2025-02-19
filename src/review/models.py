__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db import models
from django.utils import timezone
from django.db.models import Max, Q, Value
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _

from core import model_utils

from review.const import (
    EditorialDecisions as ED,
    ReviewerDecisions as RD,
    VisibilityOptions as VO
)
from utils import shared


assignment_choices = (
    ('editor', 'Editor'),
    ('section-editor', 'Section Editor'),
)


def all_review_decisions():
    """
    Review decision options presented in admin.
    """
    return (
        (RD.DECISION_ACCEPT.value, 'Accept Without Revisions'),
        (RD.DECISION_MINOR.value, 'Minor Revisions Required'),
        (RD.DECISION_MAJOR.value, 'Major Revisions Required'),
        (RD.DECISION_REJECT.value, 'Reject'),
        (RD.DECISION_NO_RECOMMENDATION.value, 'No Recommendation'),
    )


def reviewer_decision_choices():
    """
    Review decision options presented to a Reviewer.
    """
    return (
        (None, '-----------'),
        (RD.DECISION_ACCEPT.value, 'Accept Without Revisions'),
        (RD.DECISION_MINOR.value, 'Minor Revisions Required'),
        (RD.DECISION_MAJOR.value, 'Major Revisions Required'),
        (RD.DECISION_REJECT.value, 'Reject'),
    )


def review_decision():
    return (
        (ED.ACCEPT.value, 'Accept Without Revisions'),
        (ED.MINOR_REVISIONS.value, 'Minor Revisions Required'),
        (ED.MAJOR_REVISIONS.value, 'Major Revisions Required'),
        # Preserved the inconsistent verbose name below to avoid confusion to
        # existing section editors
        (ED.DECLINE.value, 'Reject'),
    )


def review_type():
    return (
        ('traditional', 'Traditional'),
        # ('annotation', 'Annotation'),
    )


def review_visibilty():
    return (
        (VO.OPEN.value, 'Open'),
        (VO.SINGLE_ANON.value, 'Single Anonymous'),
        (VO.DOUBLE_ANON.value, 'Double Anonymous')
    )


class EditorAssignment(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    editor = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    editor_type = models.CharField(max_length=20, choices=assignment_choices)
    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('article', 'editor')


class EditorAssignmentRequest(models.Model):

    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    editor = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    requesting_editor = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
        related_name='requesting_editor',
        null=True,
    )

    editor_assignment = models.ForeignKey(
        EditorAssignment,
        on_delete=models.CASCADE,
        null=True,
    )

    editor_type = models.CharField(max_length=20, choices=assignment_choices)
    notified = models.BooleanField(default=False)

    # Dates
    date_requested = models.DateTimeField(auto_now_add=True, null=True)
    date_due = models.DateField(null=True)
    date_accepted = models.DateTimeField(blank=True, null=True)
    date_declined = models.DateTimeField(blank=True, null=True)
    date_complete = models.DateTimeField(blank=True, null=True)
    date_reminded = models.DateField(blank=True, null=True)

    is_complete = models.BooleanField(default=False)


class ReviewRound(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    round_number = models.IntegerField()
    review_files = models.ManyToManyField('core.File')
    date_started = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'round_number')
        ordering = ('-round_number',)

    def __str__(self):
        return u'%s - %s round_number: %s' % (self.pk, self.article.title, self.round_number)

    def __repr__(self):
        return u'%s - %s round number: %s' % (self.pk, self.article.title, self.round_number)

    def active_reviews(self):
        return self.reviewassignment_set.exclude(
            Q(date_declined__isnull=False) | Q(decision='withdrawn')
        ).order_by(
            '-decision',
        )

    def inactive_reviews(self):
        return self.reviewassignment_set.filter(
            Q(date_declined__isnull=False) | Q(decision='withdrawn')
        ).order_by(
            'decision',
        )

    @classmethod
    def latest_article_round(cls, article):
        """ Works out and returns the latest article review round
        MS: I'm still not quite sure why it works but it does
        the round with a single query:
            SELECT "review_reviewround"."*"
            "FROM "review_reviewround"
            WHERE ("review_reviewround"."article_id" = {id}
            AND "review_reviewround"."round_number" = (
                SELECT MAX(U0."round_number") AS "latest_round"
                FROM "review_reviewround" U0 WHERE U0."article_id" = {id})
            )
            ORDER BY "review_reviewround"."round_number" DESC
        """
        latest_round = cls.objects.filter(
            article=article
        ).aggregate(
            latest_round_number=Max('round_number'),
        ).get('latest_round_number', 0)

        return cls.objects.get(article=article, round_number=latest_round)


class ReviewAssignment(models.Model):
    # FKs
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    reviewer = models.ForeignKey(
        'core.Account',
        related_name='reviewer',
        help_text='User to undertake the review',
        null=True,
        on_delete=models.SET_NULL,
    )
    editor = models.ForeignKey(
        'core.Account',
        related_name='editor',
        help_text='Editor requesting the review',
        null=True,
        on_delete=models.SET_NULL,
    )

    # Info
    review_round = models.ForeignKey(
        ReviewRound,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    decision = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=all_review_decisions(),
        verbose_name='Recommendation',
    )
    competing_interests = model_utils.JanewayBleachField(blank=True, null=True,
                                           help_text="If any of the authors or editors "
                                                     "have any competing interests please add them here. "
                                                     "EG. 'This study was paid for by corp xyz.'.")
    review_type = models.CharField(max_length=20, choices=review_type(), default='traditional',
                                   help_text='Currently only traditional, form based, review is available.')
    visibility = models.CharField(
        max_length=20, choices=review_visibilty(),
        default='double-blind',
        verbose_name=_("Anonymity"),
    )
    form = models.ForeignKey('ReviewForm', null=True, on_delete=models.SET_NULL)
    access_code = models.CharField(max_length=100, blank=True, null=True)

    # Dates
    date_requested = models.DateTimeField(auto_now_add=True)
    date_due = models.DateField()
    date_accepted = models.DateTimeField(blank=True, null=True)
    date_declined = models.DateTimeField(blank=True, null=True)
    date_complete = models.DateTimeField(blank=True, null=True)
    date_reminded = models.DateField(blank=True, null=True)

    is_complete = models.BooleanField(default=False)
    for_author_consumption = models.BooleanField(default=False)

    suggested_reviewers = models.TextField(blank=True, null=True)
    comments_for_editor = model_utils.JanewayBleachField(blank=True, null=True,
                                           help_text="If you have any comments for the Editor you can add them here; \
                                           these will not be shared with the Author.",
                                           verbose_name="Comments for the Editor")
    review_file = models.ForeignKey(
        'core.File',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    display_review_file = models.BooleanField(default=False)
    permission_to_make_public = models.BooleanField(default=False,
                                                    help_text='This journal has a policy of sharing reviews openly alongside the published article to aid in transparency. If you give permission here and the article is published, your name and review will be visible.')
    display_public = models.BooleanField(default=False, help_text='Whether this review should be publicly displayed.')

    def review_form_answers(self):
        return ReviewAssignmentAnswer.objects.filter(assignment=self).order_by('frozen_element__order')

    def save_review_form(self, review_form, assignment):
        for k, v in review_form.cleaned_data.items():
            form_element = ReviewFormElement.objects.get(reviewform=assignment.form, pk=k)
            answer, _ = ReviewAssignmentAnswer.objects.update_or_create(
                assignment=self,
                original_element=form_element,
                defaults={
                    "author_can_see": form_element.default_visibility,
                    "answer": v,
                },
            )
            form_element.snapshot(answer)

    @property
    def review_rating(self):
        try:
            return ReviewerRating.objects.get(assignment=self)
        except ReviewerRating.DoesNotExist:
            return None

    @property
    def is_late(self):
        # test if the review itself is late
        if timezone.now().date() >= self.date_due:
            return True

        return False

    @property
    def task_is_late(self):
        if self.date_accepted is not None:
            return False
        else:
            # imports are here to avoid circular dependency
            from core import models as core_models
            from utils import workflow_tasks
            active_tasks = core_models.Task.objects.filter(
                Q(content_type=ContentType.objects.get_for_model(self.article)) & Q(object_id=self.article.pk) & Q(
                    completed__isnull=True) & Q(title=workflow_tasks.DO_REVIEW_TITLE) & Q(
                    assignees=self.reviewer))

            for task in active_tasks:
                if task.is_late:
                    return True

        return False

    @property
    def status(self):
        if self.decision == RD.DECISION_WITHDRAWN.value:
            return {
                'code': 'withdrawn',
                'display': 'Withdrawn',
                'span_class': 'red',
                'date': '',
                'reminder': None,
            }
        elif self.date_complete:
            return {
                'code': 'complete',
                'display': 'Complete',
                'span_class': 'light-green',
                'date': shared.day_month(self.date_complete),
                'reminder': None,
            }
        elif self.date_accepted:
            return {
                'code': 'accept',
                'display': 'Yes',
                'span_class': 'green',
                'date': shared.day_month(self.date_accepted),
                'reminder': 'accepted',
            }
        elif self.date_declined:
            return {
                'code': 'declined',
                'display': 'No',
                'span_class': 'red',
                'date': shared.day_month(self.date_declined),
                'reminder': None,
            }
        else:
            return {
                'code': 'wait',
                'display': 'Wait',
                'span_class': 'amber',
                'date': '',
                'reminder': 'request',
            }

    def request_decision_status(self):
        if self.decision == RD.DECISION_WITHDRAWN.value:
            return f'Withdrawn {self.date_complete.date()}'
        elif self.date_accepted:
            return f'Accepted {self.date_accepted.date()}'
        elif self.date_declined:
            return f'Declined {self.date_declined.date()}'
        return 'Awaiting acknowledgement'

    def visibility_statement(self):
        if self.for_author_consumption:
            return _("available for the author to access")
        return _("not available for the author to access")

    def __str__(self):
        if self.reviewer:
            reviewer_name = self.reviewer.full_name()
        else:
            reviewer_name = "No reviewer"

        return u'{0} - Article: {1}, Reviewer: {2}'.format(
            self.id, self.article.title, reviewer_name)


class ReviewForm(models.Model):
    journal = models.ForeignKey(
        'journal.Journal',
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=200)

    intro = model_utils.JanewayBleachField(
        help_text="Message displayed at the start of the review form.",
    )
    thanks = model_utils.JanewayBleachField(
        help_text="Message displayed after the reviewer is finished.",
    )

    elements = models.ManyToManyField('ReviewFormElement')
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


def element_kind_choices():
    return (
        ('text', 'Text Field'),
        ('textarea', 'Text Area'),
        ('check', 'Check Box'),
        ('select', 'Select'),
        ('email', 'Email'),
        ('upload', 'Upload'),
        ('date', 'Date'),
    )


def element_width_choices():
    return (
        ('large-4 columns', 'third'),
        ('large-6 columns', 'half'),
        ('large-12 columns', 'full'),
    )


class BaseReviewFormElement(models.Model):
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=50, choices=element_kind_choices())
    choices = models.CharField(max_length=1000, null=True, blank=True,
                               help_text='Seperate choices with the bar | character.')
    required = models.BooleanField(default=True)
    order = models.IntegerField()
    width = models.CharField(max_length=20, choices=element_width_choices())
    help_text = model_utils.JanewayBleachField(blank=True, null=True)

    default_visibility = models.BooleanField(default=True, help_text='If true, this setting will be available '
                                                                     'to the author automatically, if false it will'
                                                                     'be hidden to the author by default.')

    class Meta:
        ordering = ('order', 'name')
        abstract = True

    def __str__(self):
        return "Element: {0} ({1})".format(self.name, self.kind)

    def choices_list(self):
        if self.choices:
            return


class ReviewFormElement(BaseReviewFormElement):
    class Meta(BaseReviewFormElement.Meta):
        pass

    def snapshot(self, answer):
        frozen, _ = FrozenReviewFormElement.objects.update_or_create(
            answer=answer,
            defaults=dict(
                form_element=self,
                name=self.name,
                kind=self.kind,
                choices=self.choices,
                required=self.required,
                order=self.order,
                width=self.width,
                help_text=self.help_text,
                default_visibility=self.default_visibility,
            )
        )
        return frozen


class ReviewAssignmentAnswer(models.Model):
    assignment = models.ForeignKey(
        ReviewAssignment,
        on_delete=models.CASCADE,
    )
    original_element = models.ForeignKey(
        ReviewFormElement,
        null=True,
        on_delete=models.SET_NULL,
    )
    answer = model_utils.JanewayBleachField(blank=True, null=True)
    edited_answer = model_utils.JanewayBleachField(null=True, blank=True)
    author_can_see = models.BooleanField(default=True)

    def __str__(self):
        return "{0}, {1}".format(self.assignment, self.element)

    @property
    def element(self):
        return self.frozen_element

    @property
    def best_label(self):
        if self.original_element:
            return self.original_element.name
        elif self.frozen_element:
            return self.frozen_element.name
        else:
            return 'element'  # this is a fallback incase the two links above are removed.


class FrozenReviewFormElement(BaseReviewFormElement):
    """ A snapshot of a review form element at the time an answer is created"""
    form_element = models.ForeignKey(
        ReviewFormElement,
        null=True,
        on_delete=models.SET_NULL,
    )
    answer = models.OneToOneField(
        ReviewAssignmentAnswer,
        related_name="frozen_element",
        on_delete=models.CASCADE,
    )

    class Meta(BaseReviewFormElement.Meta):
        pass


class ReviewFormAnswer(models.Model):
    review_assignment = models.ForeignKey(
        ReviewAssignment,
        on_delete=models.CASCADE,
    )
    form_element = models.ForeignKey(
        ReviewFormElement,
        on_delete=models.CASCADE,
    )
    answer = model_utils.JanewayBleachField()


class ReviewerRating(models.Model):
    assignment = models.OneToOneField(
        ReviewAssignment,
        on_delete=models.CASCADE,
    )
    rating = models.IntegerField(validators=[MinValueValidator(1),
                                             MaxValueValidator(10)])
    rater = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return "Reviewer: {0}, Article: {1}, Rating: {2}".format(
            self.assignment.reviewer.full_name(), self.assignment.article.title, self.rating
        )


class RevisionAction(models.Model):
    text = model_utils.JanewayBleachField()
    logged = models.DateTimeField(default=None, null=True, blank=True)
    user = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return "Revision Action by {0}: {1}".format(self.user.full_name(), self.text)


def revision_type():
    return (
        (ED.MINOR_REVISIONS.value, 'Minor Revisions'),
        (ED.MAJOR_REVISIONS.value, 'Major Revisions'),
    )


class RevisionRequest(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    editor = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
    )
    editor_note = model_utils.JanewayBleachField(
        blank=True,
        null=True,
        help_text="You can use this optional field to provide the author with "
                  "any information that may help them when evaluating the "
                  "article reviews and integrating changes into their "
                  "manuscript. This text will be displayed to the author on  "
                  "the revision page, above the reviews.",
    )
    author_note = model_utils.JanewayBleachField(
        blank=True,
        null=True,
        verbose_name="Covering Letter to Editor",
        help_text="If you would like to include a cover letter for the editor "
                  "providing changes you made to your revised manuscript, "
                  "please add this above'"
    )  # Note from Author to Editor
    actions = models.ManyToManyField(RevisionAction)  # List of actions Author took during Revision Request
    type = models.CharField(
        max_length=20,
        choices=revision_type(),
        default='minor_revisions',
    )

    response_letter = model_utils.JanewayBleachField(
        blank=True,
        null=True,
        verbose_name="Response Letter to Reviewers",
        help_text='You have the option to include a response letter for the '
                  'reviewers, providing details about the changes you made '
                  'to your manuscript or counter arguments.',
    )

    date_requested = models.DateTimeField(default=timezone.now)
    date_due = models.DateField()
    date_completed = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Revision of {0} requested by {1}".format(self.article.title, self.editor.full_name())


class EditorOverride(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    editor = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    overwritten = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "{0} overrode their access to {1}".format(self.editor.full_name(), self.article.title)


class DecisionDraft(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    editor = models.ForeignKey(
        'core.Account',
        related_name='draft_editor',
        null=True,
        on_delete=models.SET_NULL,
    )
    section_editor = models.ForeignKey(
        'core.Account',
        related_name='draft_section_editor',
        null=True,
        on_delete=models.SET_NULL,
    )
    decision = models.CharField(
        max_length=100,
        choices=review_decision(),
        verbose_name='Draft Decision',
    )
    message_to_editor = model_utils.JanewayBleachField(
        null=True,
        blank=True,
        help_text='This is the email that will be sent to the editor notifying them that you are '
                  'logging your draft decision.',
        verbose_name='Email to Editor',
    )
    email_message = model_utils.JanewayBleachField(
        null=True,
        blank=True,
        help_text='This is a draft of the email that will be sent to the author. Your editor will check this.',
        verbose_name='Draft Email to Author',
    )
    drafted = models.DateTimeField(auto_now=True)

    editor_decision = models.CharField(
        max_length=20,
        choices=((ED.ACCEPT.value, 'Accept'), (ED.DECLINE.value, 'Decline')),
        null=True,
        blank=True,
    )
    revision_request_due_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Stores a due date for a Drafted Revision Request.",
    )
    editor_decline_rationale = model_utils.JanewayBleachField(
        null=True,
        blank=True,
        help_text="Provide the section editor with a rationale for declining their drafted decision.",
        verbose_name="Rationale for Declining Draft Decision",
    )

    def __str__(self):
        return "{0}: {1}".format(self.article.title,
                                 self.decision)

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType

assignment_choices = (
    ('editor', 'Editor'),
    ('section-editor', 'Section Editor'),
)


class EditorAssignment(models.Model):
    article = models.ForeignKey('submission.Article')
    editor = models.ForeignKey('core.Account')
    editor_type = models.CharField(max_length=20, choices=assignment_choices)
    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('article', 'editor')


def review_decision():
    return (
        ('accept', 'Accept Without Revisions'),
        ('minor_revisions', 'Minor Revisions Required'),
        ('major_revisions', 'Major Revisions Required'),
        ('reject', 'Reject'),
    )


def review_type():
    return (
        ('traditional', 'Traditional'),
        #('annotation', 'Annotation'),
    )


def review_visibilty():
    return (
        ('open', 'Open'),
        ('blind', 'Single Blind'),
        ('double-blind', 'Double Blind')
    )


class ReviewRound(models.Model):
    article = models.ForeignKey('submission.Article')
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


class ReviewAssignment(models.Model):
    # FKs
    article = models.ForeignKey('submission.Article')
    reviewer = models.ForeignKey('core.Account', related_name='reviewer', help_text='User to undertake the review',
                                 null=True, on_delete=models.SET_NULL)
    editor = models.ForeignKey('core.Account', related_name='editor', help_text='Editor requesting the review',
                               null=True, on_delete=models.SET_NULL)

    # Info
    review_round = models.ForeignKey(ReviewRound, blank=True, null=True)
    decision = models.CharField(max_length=20, blank=True, null=True, choices=review_decision())
    competing_interests = models.TextField(blank=True, null=True,
                                           help_text="If any of the authors or editors "
                                                     "have any competing interests please add them here. "
                                                     "EG. 'This study was paid for by corp xyz.'.")
    review_type = models.CharField(max_length=20, choices=review_type(), default='traditional',
                                   help_text='Currently only traditional, form based, review is available.')
    visibility = models.CharField(max_length=20, choices=review_visibilty(), default='double-blind')
    form = models.ForeignKey('ReviewForm')
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
    comments_for_editor = models.TextField(blank=True, null=True,
                                           help_text="If you have any comments for the Editor you can add them here; \
                                           these will not be shared with the Author.",
                                           verbose_name="Comments for the Editor")
    review_file = models.ForeignKey('core.File', blank=True, null=True)
    display_review_file = models.BooleanField(default=False)

    def review_form_answers(self):
        return ReviewAssignmentAnswer.objects.filter(assignment=self).order_by('element__order')

    def save_review_form(self, review_form, assignment):
        for k, v in review_form.cleaned_data.items():
            form_element = ReviewFormElement.objects.get(reviewform=assignment.form, name=k)
            ReviewAssignmentAnswer.objects.create(
                assignment=self,
                element=form_element,
                answer=v,
                author_can_see=form_element.default_visibility,
            )

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

    def __str__(self):
        return u'{0} - Article: {1}, Reviewer: {2}'.format(self.id, self.article.title, self.reviewer.full_name())


class ReviewForm(models.Model):
    journal = models.ForeignKey('journal.Journal')

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)

    intro = models.TextField(help_text="Message displayed at the start of the review form.")
    thanks = models.TextField(help_text="Message displayed after the reviewer is finished.")

    elements = models.ManyToManyField('ReviewFormElement')

    def __str__(self):
        return u'{0} - {1}'.format(self.id, self.name)


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


class ReviewFormElement(models.Model):
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=50, choices=element_kind_choices())
    choices = models.CharField(max_length=1000, null=True, blank=True,
                               help_text='Seperate choices with the bar | character.')
    required = models.BooleanField(default=True)
    order = models.IntegerField()
    width = models.CharField(max_length=20, choices=element_width_choices())
    help_text = models.TextField(blank=True, null=True)

    default_visibility = models.BooleanField(default=True, help_text='If true, this setting will be available '
                                                                     'to the author automatically, if false it will'
                                                                     'be hidden to the author by default.')

    def __str__(self):
        return "Element: {0} ({1})".format(self.name, self.kind)

    def choices_list(self):
        if self.choices:
            return


class ReviewAssignmentAnswer(models.Model):
    assignment = models.ForeignKey(ReviewAssignment)
    element = models.ForeignKey(ReviewFormElement)
    answer = models.TextField()
    edited_answer = models.TextField(null=True, blank=True)
    author_can_see = models.BooleanField(default=True)

    def __str__(self):
        return "{0}, {1}".format(self.assignment, self.element)


class ReviewFormAnswer(models.Model):
    review_assignment = models.ForeignKey(ReviewAssignment)
    form_element = models.ForeignKey(ReviewFormElement)
    answer = models.TextField()


class ReviewerRating(models.Model):
    assignment = models.OneToOneField(ReviewAssignment)
    rating = models.IntegerField(validators=[MinValueValidator(1),
                                             MaxValueValidator(10)])
    rater = models.ForeignKey('core.Account')

    def __str__(self):
        return "Reviewer: {0}, Article: {1}, Rating: {2}".format(
            self.assignment.reviewer.full_name(), self.assignment.article.title, self.rating
        )


class RevisionAction(models.Model):
    text = models.TextField()
    logged = models.DateTimeField(default=None, null=True, blank=True)
    user = models.ForeignKey('core.Account')

    def __str__(self):
        return "Revision Action by {0}: {1}".format(self.user.full_name(), self.text)


def revision_type():
    return (
        ('minor_revisions', 'Minor Revisions'),
        ('major_revisions', 'Major Revisions'),
    )


class RevisionRequest(models.Model):
    article = models.ForeignKey('submission.Article')
    editor = models.ForeignKey('core.Account')
    editor_note = models.TextField()  # Note from Editor to Author
    author_note = models.TextField(blank=True, null=True, verbose_name="Covering Letter")  # Note from Author to Editor
    actions = models.ManyToManyField(RevisionAction)  # List of actions Author took during Revision Request
    type = models.CharField(max_length=20, choices=revision_type(), default='minor_revisions')

    date_requested = models.DateField(default=timezone.now)
    date_due = models.DateField()
    date_completed = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Revision of {0} requested by {1}".format(self.article.title, self.editor.full_name())


class EditorOverride(models.Model):
    article = models.ForeignKey('submission.Article')
    editor = models.ForeignKey('core.Account')
    overwritten = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "{0} overrode their access to {1}".format(self.editor.full_name(), self.article.title)


class DecisionDraft(models.Model):
    article = models.ForeignKey('submission.Article')
    section_editor = models.ForeignKey('core.Account', related_name='draft_section_editor')
    decision = models.CharField(max_length=100, choices=review_decision())
    message_to_editor = models.TextField(null=True, blank=True)
    email_message = models.TextField(null=True, blank=True)
    drafted = models.DateTimeField(auto_now=True)

    editor_decision = models.CharField(max_length=20,
                                       choices=(('accept', 'Accept'), ('decline', 'Decline')),
                                       null=True,
                                       blank=True)
    closed = models.BooleanField(default=False)

    def __str__(self):
        return "{0}: {1}".format(self.article.title,
                                 self.decision)

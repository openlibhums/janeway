__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from django.db import models
from django.db.models import Max, Q
from django.utils import timezone
from django.utils.translation import gettext as _

from core import model_utils
from screening.const import (
    ScreeningRecommendations as SR,
    all_screener_recommendations,
    screening_revision_type_choices,
)
from utils import shared


def element_kind_choices():
    return (
        ("text", "Text Field"),
        ("textarea", "Text Area"),
        ("check", "Check Box"),
        ("select", "Select"),
        ("email", "Email"),
        ("upload", "Upload"),
        ("date", "Date"),
    )


class ScreeningRound(models.Model):
    article = models.ForeignKey(
        "submission.Article",
        on_delete=models.CASCADE,
    )
    round_number = models.IntegerField()
    date_started = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("article", "round_number")
        ordering = ("-round_number",)

    def __str__(self):
        return "%s - %s round_number: %s" % (
            self.pk,
            self.article.title,
            self.round_number,
        )

    def active_screenings(self):
        return self.screeningassignment_set.exclude(
            Q(date_declined__isnull=False) | Q(recommendation=SR.WITHDRAWN.value)
        ).order_by("-recommendation")

    def inactive_screenings(self):
        return self.screeningassignment_set.filter(
            Q(date_declined__isnull=False) | Q(recommendation=SR.WITHDRAWN.value)
        ).order_by("recommendation")

    @classmethod
    def latest_article_round(cls, article):
        """Return the most recent ScreeningRound for an article."""
        latest_round_number = (
            cls.objects.filter(article=article)
            .aggregate(latest_round_number=Max("round_number"))
            .get("latest_round_number", 0)
        )
        return cls.objects.get(article=article, round_number=latest_round_number)

    @property
    def completion_summary(self):
        """Return (complete_count, total_count) for live (not withdrawn /
        declined) assignments on this round, used to render the per-round
        tab label as e.g. 'Round 1 (2 / 3)'."""
        active = self.screeningassignment_set.exclude(
            Q(date_declined__isnull=False) | Q(recommendation=SR.WITHDRAWN.value),
        )
        return (
            active.filter(is_complete=True).count(),
            active.count(),
        )


class ScreeningAssignment(models.Model):
    """A request to a member of the editorial team to screen a submission.

    Distinct from ReviewAssignment: a screener is internal editorial staff
    (not an external peer reviewer), screening reports are never published,
    and anonymity is configured per-assignment rather than per-round.
    """

    # FKs
    article = models.ForeignKey(
        "submission.Article",
        on_delete=models.CASCADE,
    )
    screener = models.ForeignKey(
        "core.Account",
        related_name="screener_assignments",
        help_text="User to undertake the screening report",
        null=True,
        on_delete=models.SET_NULL,
    )
    editor = models.ForeignKey(
        "core.Account",
        related_name="editor_screening_assignments",
        help_text="Editor requesting the screening report",
        null=True,
        on_delete=models.SET_NULL,
    )
    screening_round = models.ForeignKey(
        ScreeningRound,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    form = models.ForeignKey("ScreeningForm", null=True, on_delete=models.SET_NULL)

    # Recommendation + conditional reviewer suggestion
    recommendation = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        choices=all_screener_recommendations(),
        verbose_name="Recommendation",
    )
    suggested_reviewers = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "If recommending the article for peer review, the screener may "
            "suggest reviewers here. Hidden from the author."
        ),
    )

    anonymous_to_author = models.BooleanField(
        default=True,
        help_text="Hide the screener's name from the corresponding author.",
    )
    anonymous_to_coscreeners = models.BooleanField(
        default=False,
        help_text="Hide the screener's name from other screeners on this round.",
    )

    comments_for_editor = model_utils.JanewayBleachField(
        blank=True,
        null=True,
        help_text=(
            "Comments visible only to the managing editor; will not be "
            "shared with the author."
        ),
        verbose_name="Comments for the Editor",
    )

    date_requested = models.DateTimeField(auto_now_add=True)
    date_due = models.DateField()
    date_accepted = models.DateTimeField(blank=True, null=True)
    date_declined = models.DateTimeField(blank=True, null=True)
    date_complete = models.DateTimeField(blank=True, null=True)

    is_complete = models.BooleanField(default=False)

    def __str__(self):
        screener_name = self.screener.full_name() if self.screener else "No screener"
        return "{0} - Article: {1}, Screener: {2}".format(
            self.id, self.article.title, screener_name
        )

    def screening_form_answers(self):
        return ScreeningAssignmentAnswer.objects.filter(assignment=self).order_by(
            "frozen_element__order",
        )

    def save_screening_form(self, screening_form):
        elements_by_pk = {
            str(e.pk): e
            for e in ScreeningFormElement.objects.filter(screeningform=self.form)
        }
        for k, v in screening_form.cleaned_data.items():
            form_element = elements_by_pk[str(k)]
            answer, _ = ScreeningAssignmentAnswer.objects.update_or_create(
                assignment=self,
                original_element=form_element,
                defaults={"answer": v},
            )
            form_element.snapshot(answer)

    def screener_display(self, viewer=None):
        """Return the screener's display name, honouring anonymity flags.

        Editorial staff always see the real name. The corresponding author
        and other screeners are subject to the per-assignment anonymity
        booleans.
        """
        real_name = self.screener.full_name() if self.screener else "Unknown"
        if viewer is None:
            return real_name

        if self.anonymous_to_author and viewer == self.article.correspondence_author:
            return _("Anonymous screener")

        if self.anonymous_to_coscreeners and self.screening_round:
            co_screener_ids = self.screening_round.screeningassignment_set.exclude(
                pk=self.pk,
            ).values_list("screener_id", flat=True)
            if viewer and viewer.pk in co_screener_ids:
                return _("Anonymous screener")

        return real_name

    @property
    def is_withdrawn(self):
        return self.recommendation == SR.WITHDRAWN.value

    @property
    def is_declined(self):
        return self.date_declined is not None and not self.is_withdrawn

    @property
    def is_late(self):
        days = self.days_until_due
        if days is None:
            return False
        return days <= 0

    @property
    def days_until_due(self):
        """Signed number of days from today to the due date. Negative
        when overdue, zero on the day, positive when due in the future.
        Returns None if the assignment has no due date or the value is
        not comparable to a date."""
        import datetime as _dt

        due = self.date_due
        if due is None:
            return None
        # date_due is declared as DateField, but historical rows or
        # bad data could store a datetime. Normalise to date before
        # comparing.
        if isinstance(due, _dt.datetime):
            due = due.date()
        if not isinstance(due, _dt.date):
            return None
        try:
            return (due - timezone.now().date()).days
        except (TypeError, ValueError):
            return None

    @property
    def status(self):
        if self.recommendation == SR.WITHDRAWN.value:
            return {
                "code": "withdrawn",
                "display": "Withdrawn",
                "span_class": "alert",
                "date": "",
                "reminder": None,
            }
        if self.date_complete and self.date_accepted:
            return {
                "code": "complete",
                "display": "Complete",
                "span_class": "success",
                "date": shared.day_month(self.date_complete),
                "reminder": None,
            }
        if self.date_accepted:
            return {
                "code": "accept",
                "display": "Accepted",
                "span_class": "success",
                "date": shared.day_month(self.date_accepted),
                "reminder": "accepted",
            }
        if self.date_declined:
            return {
                "code": "declined",
                "display": "Declined",
                "span_class": "alert",
                "date": shared.day_month(self.date_declined),
                "reminder": None,
            }
        return {
            "code": "wait",
            "display": "Awaiting Response",
            "span_class": "warning",
            "date": "",
            "reminder": "request",
        }


class ScreeningForm(models.Model):
    journal = models.ForeignKey(
        "journal.Journal",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=200)
    intro = model_utils.JanewayBleachField(
        help_text="Message displayed at the start of the screening form.",
    )
    thanks = model_utils.JanewayBleachField(
        help_text="Message displayed after the screener is finished.",
    )
    elements = models.ManyToManyField("ScreeningFormElement")
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class BaseScreeningFormElement(models.Model):
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=50, choices=element_kind_choices())
    choices = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Separate choices with the bar | character.",
    )
    required = models.BooleanField(default=True)
    order = models.IntegerField()
    help_text = model_utils.JanewayBleachField(blank=True, null=True)
    default_visibility = models.BooleanField(
        default=True,
        help_text=(
            "If true, this answer will be available to the author by "
            "default; if false, it will be hidden from the author."
        ),
    )

    class Meta:
        ordering = ("order", "name")
        abstract = True

    def __str__(self):
        return "Element: {0} ({1})".format(self.name, self.kind)


class ScreeningFormElement(BaseScreeningFormElement):
    class Meta(BaseScreeningFormElement.Meta):
        pass

    def snapshot(self, answer):
        frozen, _ = FrozenScreeningFormElement.objects.update_or_create(
            answer=answer,
            defaults=dict(
                form_element=self,
                name=self.name,
                kind=self.kind,
                choices=self.choices,
                required=self.required,
                order=self.order,
                help_text=self.help_text,
                default_visibility=self.default_visibility,
            ),
        )
        return frozen


class ScreeningAssignmentAnswer(models.Model):
    assignment = models.ForeignKey(
        ScreeningAssignment,
        on_delete=models.CASCADE,
    )
    original_element = models.ForeignKey(
        ScreeningFormElement,
        null=True,
        on_delete=models.SET_NULL,
    )
    answer = model_utils.JanewayBleachField(blank=True, null=True)

    def __str__(self):
        return "{0}, {1}".format(self.assignment, self.best_label)

    @property
    def element(self):
        return self.frozen_element

    @property
    def best_label(self):
        if self.original_element:
            return self.original_element.name
        if getattr(self, "frozen_element", None):
            return self.frozen_element.name
        return "element"


class FrozenScreeningFormElement(BaseScreeningFormElement):
    """A snapshot of a screening form element at the time an answer is
    created. Preserves the question label and shape so that subsequent
    edits to the live form do not corrupt historical answers."""

    form_element = models.ForeignKey(
        ScreeningFormElement,
        null=True,
        on_delete=models.SET_NULL,
    )
    answer = models.OneToOneField(
        ScreeningAssignmentAnswer,
        related_name="frozen_element",
        on_delete=models.CASCADE,
    )

    class Meta(BaseScreeningFormElement.Meta):
        pass


class ScreeningRevisionRequest(models.Model):
    """Author revision triggered by a screening decision.

    The editor opens a revision request from the screening article page;
    the author lands on a dedicated screening revision page, uploads
    revised files via the article's file machinery, optionally adds a
    covering letter, and submits. A fresh ScreeningRound is opened on
    submission so the same screener(s) can re-screen the revision.
    """

    article = models.ForeignKey(
        "submission.Article",
        on_delete=models.CASCADE,
    )
    editor = models.ForeignKey(
        "core.Account",
        null=True,
        on_delete=models.SET_NULL,
    )
    editor_note = model_utils.JanewayBleachField(
        blank=True,
        null=True,
        verbose_name="Note to Author",
        help_text=(
            "Description of the changes the author should make. Shown to "
            "the author on the revision page."
        ),
    )
    author_note = model_utils.JanewayBleachField(
        blank=True,
        null=True,
        verbose_name="Covering Letter",
        help_text=(
            "Optional covering letter from the author describing the changes they made."
        ),
    )
    type = models.CharField(
        max_length=40,
        choices=screening_revision_type_choices(),
        default="minor_revisions",
    )

    date_requested = models.DateTimeField(default=timezone.now)
    date_due = models.DateField()
    date_completed = models.DateTimeField(blank=True, null=True)
    date_cancelled = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        editor_name = self.editor.full_name() if self.editor else "Unknown editor"
        return "Screening revision of {0} requested by {1}".format(
            self.article.title,
            editor_name,
        )

    @property
    def is_complete(self):
        return self.date_completed is not None

    @property
    def is_cancelled(self):
        return self.date_cancelled is not None

    @property
    def is_open(self):
        return not self.is_complete and not self.is_cancelled


class ScreeningPool(models.Model):
    """Per-journal selection of editorial groups whose members are
    eligible to be invited as screeners. When no groups are selected
    the pool falls back to all editor and section-editor role-holders
    on the journal."""

    journal = models.OneToOneField(
        "journal.Journal",
        on_delete=models.CASCADE,
        related_name="screening_pool",
    )
    groups = models.ManyToManyField(
        "core.EditorialGroup",
        blank=True,
        help_text=(
            "Editorial groups whose members appear in the screener "
            "selection list. Leave empty to fall back to the journal's "
            "editor / section-editor role-holders."
        ),
    )

    def __str__(self):
        return "Screening pool for {0}".format(self.journal.code)


class TechnicalChecklistTemplate(models.Model):
    """A journal-level template of items that screeners run through during
    the technical check. One template per journal can be marked default;
    that default is auto-applied to each article entering Screening.
    """

    journal = models.ForeignKey(
        "journal.Journal",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=200)
    is_default = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ("-is_default", "name")

    def __str__(self):
        return "{0} ({1})".format(self.name, self.journal.code)


class TechnicalChecklistTemplateItem(models.Model):
    template = models.ForeignKey(
        TechnicalChecklistTemplate,
        on_delete=models.CASCADE,
        related_name="items",
    )
    label = models.CharField(max_length=255)
    help_text = models.CharField(max_length=500, blank=True, default="")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ("order", "label")

    def __str__(self):
        return self.label


class TechnicalChecklist(models.Model):
    """The per-article instantiation of a TechnicalChecklistTemplate. Each
    article in Screening gets at most one checklist, derived from the
    journal's default template at the moment of first visit."""

    article = models.OneToOneField(
        "submission.Article",
        on_delete=models.CASCADE,
        related_name="technical_checklist",
    )
    template = models.ForeignKey(
        TechnicalChecklistTemplate,
        on_delete=models.SET_NULL,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Checklist for {0}".format(self.article.title)


class TechnicalChecklistItem(models.Model):
    checklist = models.ForeignKey(
        TechnicalChecklist,
        on_delete=models.CASCADE,
        related_name="items",
    )
    template_item = models.ForeignKey(
        TechnicalChecklistTemplateItem,
        on_delete=models.SET_NULL,
        null=True,
    )
    label = models.CharField(max_length=255)
    is_complete = models.BooleanField(default=False)
    comment = models.TextField(blank=True, default="")
    completed_by = models.ForeignKey(
        "core.Account",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ("order", "label")

    def __str__(self):
        return "{0}: {1}".format(
            self.checklist.article.title,
            self.label,
        )

__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


import datetime

from django import forms
from django.utils.safestring import mark_safe

from screening import logic, models
from screening.const import screener_recommendation_choices
from utils.forms import HTMLDateInput


class ScreeningAssignmentForm(forms.ModelForm):
    """Form for inviting a screener to a round.

    The screener choice list is restricted to the journal's editorial team
    and excludes anyone already assigned to this round.
    """

    class Meta:
        model = models.ScreeningAssignment
        fields = (
            "screener",
            "form",
            "date_due",
            "anonymous_to_author",
            "anonymous_to_coscreeners",
        )
        widgets = {"date_due": HTMLDateInput}

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop("article")
        self.journal = kwargs.pop("journal")
        self.screening_round = kwargs.pop("screening_round")
        self.editor = kwargs.pop("editor")
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            del self.fields["screener"]
        else:
            already_assigned_ids = list(
                logic.current_screeners_on_round(self.screening_round).values_list(
                    "pk",
                    flat=True,
                )
            )
            self.fields["screener"].queryset = logic.eligible_screeners(
                self.journal,
                exclude_user_ids=already_assigned_ids,
            )
        self.fields["form"].queryset = models.ScreeningForm.objects.filter(
            journal=self.journal,
            deleted=False,
        )
        self.fields["form"].required = False

        if not self.initial.get("date_due"):
            self.fields["date_due"].initial = (
                datetime.date.today() + datetime.timedelta(days=14)
            )

    def save(self, commit=True):
        assignment = super().save(commit=False)
        assignment.article = self.article
        assignment.screening_round = self.screening_round
        assignment.editor = self.editor
        if commit:
            assignment.save()
        return assignment


def _field_for_element(element):
    """Build a Django form field that matches the shape of a
    ScreeningFormElement. Mirrors review's GeneratedForm pattern; kept
    minimal to the kinds in production use."""
    kind = element.kind
    common = {
        "label": element.name,
        "required": element.required,
        "help_text": mark_safe(element.help_text) if element.help_text else "",
    }
    if kind == "text":
        return forms.CharField(**common)
    if kind == "textarea":
        return forms.CharField(widget=forms.Textarea, **common)
    if kind == "check":
        return forms.BooleanField(**{**common, "required": False})
    if kind == "select":
        raw_choices = (element.choices or "").split("|")
        choices = [
            (choice.strip(), choice.strip()) for choice in raw_choices if choice.strip()
        ]
        return forms.ChoiceField(choices=choices, **common)
    if kind == "email":
        return forms.EmailField(**common)
    if kind == "date":
        return forms.DateField(**common)
    if kind == "upload":
        return forms.FileField(**common)
    return forms.CharField(**common)


def build_screening_form_class(screening_form):
    """Return a dynamic Django Form class whose fields match the
    elements declared on the given ScreeningForm. Field keys are the
    integer PK of each ScreeningFormElement so the view can map answers
    back to the element when saving."""
    field_map = {}
    for element in screening_form.elements.all().order_by("order"):
        field_map[str(element.pk)] = _field_for_element(element)
    return type("DynamicScreeningForm", (forms.Form,), field_map)


class ScreeningPoolForm(forms.ModelForm):
    """Manager-side form letting a journal select the editorial groups
    that make up the screener pool."""

    class Meta:
        model = models.ScreeningPool
        fields = ("groups",)
        widgets = {"groups": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        journal = kwargs.pop("journal")
        super().__init__(*args, **kwargs)
        from core import models as core_models

        self.fields["groups"].queryset = core_models.EditorialGroup.objects.filter(
            journal=journal,
        )
        self.fields["groups"].label = "Editorial groups whose members may screen"


class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = models.TechnicalChecklistTemplate
        exclude = ("journal", "deleted")


class ChecklistTemplateItemForm(forms.ModelForm):
    class Meta:
        model = models.TechnicalChecklistTemplateItem
        exclude = ("template",)


class NewScreeningForm(forms.ModelForm):
    """Manager-side form to create / edit a ScreeningForm (the
    container for elements)."""

    class Meta:
        model = models.ScreeningForm
        exclude = ("journal", "elements", "deleted")


class ScreeningElementForm(forms.ModelForm):
    """Manager-side form to create / edit a single ScreeningFormElement."""

    class Meta:
        model = models.ScreeningFormElement
        exclude = ("",)


class ScreeningRevisionRequestForm(forms.ModelForm):
    """Editor-side form to request revisions from the author after
    screening. Captures the editor's note, due date, and severity."""

    class Meta:
        model = models.ScreeningRevisionRequest
        fields = ("type", "editor_note", "date_due")
        widgets = {"date_due": HTMLDateInput}

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop("article")
        self.editor = kwargs.pop("editor")
        super().__init__(*args, **kwargs)
        self.fields["editor_note"].required = True
        if not self.initial.get("date_due"):
            self.fields["date_due"].initial = (
                datetime.date.today() + datetime.timedelta(days=14)
            )

    def save(self, commit=True):
        revision = super().save(commit=False)
        revision.article = self.article
        revision.editor = self.editor
        if commit:
            revision.save()
        return revision


class AuthorRevisionResponseForm(forms.ModelForm):
    """Author-side form to submit a revised manuscript file plus an
    optional covering letter. The uploaded file is saved as a new
    manuscript file on the article via core.files.save_file_to_article."""

    manuscript = forms.FileField(
        required=True,
        label="Revised manuscript",
        help_text="Upload the revised manuscript as a single file.",
    )

    class Meta:
        model = models.ScreeningRevisionRequest
        fields = ("author_note",)


class ScreeningRecommendationForm(forms.Form):
    """The screener's final recommendation, captured alongside their
    answers to the screening form."""

    recommendation = forms.ChoiceField(
        choices=screener_recommendation_choices(),
        required=True,
        label="Recommendation",
    )
    suggested_reviewers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        label="Suggested reviewers",
        help_text=(
            "If recommending the article for peer review, you may suggest "
            "reviewers here. These suggestions are hidden from the author."
        ),
    )
    comments_for_editor = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        label="Comments for the editor",
        help_text=(
            "Visible only to the managing editor; will not be shared with the author."
        ),
    )

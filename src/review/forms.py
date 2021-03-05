__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from datetime import timedelta

from django import forms
from django.utils import timezone
from django.template.defaultfilters import linebreaksbr

from review import models
from review.logic import render_choices
from core import models as core_models
from utils import setting_handler
from utils.forms import FakeModelForm


class DraftDecisionForm(forms.ModelForm):
    class Meta:
        model = models.DecisionDraft
        exclude = ('section_editor', 'article', 'editor_decision', 'closed')

    def __init__(self, *args, **kwargs):
        email_message = kwargs.pop('email_message', None)
        super(DraftDecisionForm, self).__init__(*args, **kwargs)
        self.fields['email_message'].initial = linebreaksbr(email_message)


class ReviewAssignmentForm(forms.ModelForm):
    class Meta:
        model = models.ReviewAssignment
        fields = ('review_type', 'visibility', 'form', 'date_due')

    def __init__(self, *args, **kwargs):
        journal = kwargs.pop('journal', None)
        super(ReviewAssignmentForm, self).__init__(*args, **kwargs)
        default_visibility = setting_handler.get_setting('general', 'default_review_visibility', journal, create=True)
        default_due = setting_handler.get_setting('general', 'default_review_days', journal, create=True).value
        default_form = setting_handler.get_setting('general',
                                                   'default_review_form', journal, create=True).processed_value

        if journal:
            self.fields['form'].queryset = models.ReviewForm.objects.filter(journal=journal, deleted=False)

        if default_visibility.value:
            self.fields['visibility'].initial = default_visibility.value

        if default_due:
            due_date = timezone.now() + timedelta(days=int(default_due))
            self.fields['date_due'].initial = due_date

        if default_form:
            form = models.ReviewForm.objects.get(pk=default_form)
            self.fields['form'].initial = form


class ReviewerDecisionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        decision_required = kwargs.pop("decision_required", False)
        super().__init__(*args, **kwargs)
        self.fields['decision'].required = decision_required

    class Meta:
        model = models.ReviewAssignment
        fields = ('decision', 'comments_for_editor')


class FakeReviewerDecisionForm(FakeModelForm, ReviewerDecisionForm):

    def __init__(self, *args, **kwargs):
        kwargs["disable_fields"] = True
        super().__init__(*args, **kwargs)


class ReplacementFileDetails(forms.ModelForm):
    class Meta:
        model = core_models.File
        fields = (
            'label',
            'description',
        )


class SuggestReviewers(forms.ModelForm):
    class Meta:
        model = models.ReviewAssignment
        fields = (
            'suggested_reviewers',
        )


class RevisionRequest(forms.ModelForm):
    class Meta:
        model = models.RevisionRequest
        fields = (
            'date_due', 'type', 'editor_note',
        )


class EditRevisionDue(forms.ModelForm):
    class Meta:
        model = models.RevisionRequest
        fields = (
            'date_due',
        )


class DoRevisions(forms.ModelForm):
    class Meta:
        model = models.RevisionRequest
        fields = (
            'author_note',
        )


class GeneratedForm(forms.Form):
    def __init__(self, *args, **kwargs):
        review_assignment = kwargs.pop('review_assignment', None)
        fields_required = kwargs.pop('fields_required', True)
        answer = kwargs.pop('answer', None)
        preview = kwargs.pop('preview', None)
        if 'initial' not in kwargs and review_assignment:
            kwargs["initial"] = {
                a.original_element.name: a.answer
                for a in review_assignment.review_form_answers()
                if a.original_element
            }
        super(GeneratedForm, self).__init__(*args, **kwargs)

        if answer:
            elements = [answer.element]
        elif preview:
            elements = preview.elements.all()
        else:
            elements = review_assignment.form.elements.all()

        for element in elements:
            if element.kind == 'text':
                self.fields[element.name] = forms.CharField(
                    widget=forms.TextInput(attrs={'div_class': element.width}),
                    required=element.required if fields_required else False)
            elif element.kind == 'textarea':
                self.fields[element.name] = forms.CharField(widget=forms.Textarea,
                                                            required=element.required if fields_required else False)
            elif element.kind == 'date':
                self.fields[element.name] = forms.CharField(
                    widget=forms.DateInput(attrs={'class': 'datepicker', 'div_class': element.width}),
                    required=element.required if fields_required else False)
            elif element.kind == 'upload':
                self.fields[element.name] = forms.FileField(required=element.required if fields_required else False)
            elif element.kind == 'select':
                choices = render_choices(element.choices)
                self.fields[element.name] = forms.ChoiceField(
                    widget=forms.Select(attrs={'div_class': element.width}), choices=choices,
                    required=element.required if fields_required else False)
            elif element.kind == 'email':
                self.fields[element.name] = forms.EmailField(
                    widget=forms.TextInput(attrs={'div_class': element.width}),
                    required=element.required if fields_required else False)
            elif element.kind == 'check':
                self.fields[element.name] = forms.BooleanField(
                    widget=forms.CheckboxInput(attrs={'is_checkbox': True}),
                    required=element.required if fields_required else False)

            self.fields[element.name].help_text = element.help_text
            self.fields[element.name].label = element.name

            if answer:
                self.fields[element.name].initial = answer.edited_answer if answer.edited_answer else answer.answer


class NewForm(forms.ModelForm):
    class Meta:
        model = models.ReviewForm
        exclude = ('journal', 'elements', 'deleted')


class ElementForm(forms.ModelForm):
    class Meta:
        model = models.ReviewFormElement
        exclude = ('',)


class ReviewReminderForm(forms.Form):
    subject = forms.CharField(max_length=255, required=True)
    body = forms.CharField(widget=forms.Textarea, required=True)

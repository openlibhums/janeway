__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from datetime import timedelta
from uuid import uuid4

from django_summernote.widgets import SummernoteWidget

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.template.defaultfilters import linebreaksbr

from review import models, logic
from core import models as core_models, forms as core_forms
from utils import setting_handler
from utils.forms import FakeModelForm, HTMLDateInput, HTMLSwitchInput


class DraftDecisionForm(forms.ModelForm):
    widgets = {'revision_request_due_date': HTMLDateInput()}

    class Meta:
        model = models.DecisionDraft
        exclude = (
            'section_editor', 'article', 'editor_decision'
        )

    def __init__(self, *args, **kwargs):
        newly_created = kwargs.get('instance') is None
        message_to_editor = kwargs.pop('message_to_editor', None)
        editors = kwargs.pop('editors', [])
        super(DraftDecisionForm, self).__init__(*args, **kwargs)
        self.fields['message_to_editor'].initial = linebreaksbr(message_to_editor)
        self.fields['revision_request_due_date'].widget = HTMLDateInput()
        self.fields['revision_request_due_date'].widget.attrs['onchange'] = 'decision_change()'
        self.fields['decision'].widget.attrs[
            'onchange'] = 'decision_change()'
        self.fields['editor'].queryset = editors
        if not newly_created:
            self.fields['message_to_editor'].widget = forms.HiddenInput()
            self.fields['editor'].widget = forms.HiddenInput()


class ReviewAssignmentForm(forms.ModelForm, core_forms.ConfirmableIfErrorsForm):
    class Meta:
        model = models.ReviewAssignment
        fields = ('visibility', 'form', 'date_due', 'reviewer')

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal', None)
        self.article = kwargs.pop('article')
        self.editor = kwargs.pop('editor')
        self.reviewers = kwargs.pop('reviewers')

        super(ReviewAssignmentForm, self).__init__(*args, **kwargs)

        self.fields['form'].empty_label = None
        default_visibility = setting_handler.get_setting(
            'general',
            'default_review_visibility',
            self.journal,
            create=True,
        )
        default_due = setting_handler.get_setting(
            'general',
            'default_review_days',
            self.journal,
            create=True,
        ).value
        default_form = setting_handler.get_setting(
            'general',
            'default_review_form',
            self.journal,
            create=True,
        ).processed_value

        if self.journal:
            self.fields['form'].queryset = models.ReviewForm.objects.filter(journal=self.journal, deleted=False)

        if default_visibility.value:
            self.fields['visibility'].initial = default_visibility.value

        if default_due:
            due_date = timezone.now() + timedelta(days=int(default_due))
            self.fields['date_due'].initial = due_date

        if default_form and not self.instance.form:
            form = models.ReviewForm.objects.get(pk=default_form)
            self.fields['form'].initial = form

        if self.reviewers:
            self.fields['reviewer'].queryset = self.reviewers

        if self.instance.date_accepted:
            # Form should not be changed after request has been accepted
            self.fields['form'].initial = self.instance.form
            self.fields['form'].disabled = True

    def save(self, commit=True):
        review_assignment = super().save(commit=False)
        review_assignment.editor = self.editor
        review_assignment.article = self.article
        review_assignment.review_round = self.article.current_review_round_object()
        review_assignment.access_code = uuid4()

        if commit:
            review_assignment.save()

        return review_assignment

    def check_for_potential_errors(self):
        # This customizes the confirmable form method
        potential_errors = []

        one_click_access = setting_handler.get_setting('general', 'enable_one_click_access', self.journal).value
        if not one_click_access:
            reviewer = self.cleaned_data.get('reviewer', None)
            message = self.check_for_inactive_account(reviewer)
            if message:
                potential_errors.append(message)

        return potential_errors


class EditReviewAssignmentForm(forms.ModelForm):
    class Meta:
        model = models.ReviewAssignment
        fields = ('visibility', 'form', 'date_due')

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal', None)
        super(EditReviewAssignmentForm, self).__init__(*args, **kwargs)
        if self.journal:
            self.fields['form'].queryset = models.ReviewForm.objects.filter(journal=self.journal, deleted=False)


class ReviewerDecisionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        decision_required = kwargs.pop("decision_required", False)
        super().__init__(*args, **kwargs)
        self.fields['decision'].required = decision_required

    class Meta:
        model = models.ReviewAssignment
        fields = ('decision', 'comments_for_editor', 'permission_to_make_public')


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


class RevisionRequest(forms.ModelForm, core_forms.ConfirmableIfErrorsForm):
    QUESTION = _('Are you sure you want to request revisions?')

    class Meta:
        model = models.RevisionRequest
        fields = (
            'date_due', 'type', 'editor_note',
        )

    def __init__(self, *args, **kwargs):
        self.editor = kwargs.pop('editor', None)
        self.article = kwargs.pop('article', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        revision_request = super().save(commit=False)
        revision_request.editor = self.editor
        revision_request.article = self.article

        if commit:
            revision_request.save()

        return revision_request

    def check_for_potential_errors(self):
        potential_errors = []

        message = self.check_for_inactive_account(self.article.correspondence_author)
        if message:
            potential_errors.append(message)

        return potential_errors


class EditRevisionDue(forms.ModelForm):
    class Meta:
        model = models.RevisionRequest
        fields = (
            'date_due',
        )


class DoRevisions(forms.ModelForm, core_forms.ConfirmableForm):

    # Confirmable form constants
    QUESTION = _('Are you sure you want to complete the revision request?')

    class Meta:
        model = models.RevisionRequest
        fields = (
            'author_note',
        )
        widgets = {
            'author_note': SummernoteWidget(),
        }

    def check_for_potential_errors(self):
        # This customizes the confirmable form method
        potential_errors = []

        if not self.cleaned_data.get('author_note', None):
            message = 'The Covering Letter field is empty.'
            potential_errors.append(_(message))

        ms_files = self.instance.article.manuscript_files.all()
        if ms_files:
            last_upload = max(set(ms_file.date_uploaded for ms_file in ms_files))
            if self.instance.date_requested > last_upload:
                message = 'No manuscript files have been replaced or added.'
                potential_errors.append(_(message))
        else:
            message = 'No manuscript files have been uploaded.'
            potential_errors.append(_(message))

        return potential_errors


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
                self.fields[str(element.pk)] = forms.CharField(
                    widget=forms.TextInput(attrs={'div_class': element.width}),
                    required=element.required if fields_required else False)
            elif element.kind == 'textarea':
                self.fields[str(element.pk)] = forms.CharField(widget=forms.Textarea,
                                                            required=element.required if fields_required else False)
            elif element.kind == 'date':
                self.fields[str(element.pk)] = forms.CharField(
                    widget=forms.DateInput(attrs={'class': 'datepicker', 'div_class': element.width}),
                    required=element.required if fields_required else False)
            elif element.kind == 'upload':
                self.fields[str(element.pk)] = forms.FileField(required=element.required if fields_required else False)
            elif element.kind == 'select':
                choices = logic.render_choices(element.choices)
                self.fields[str(element.pk)] = forms.ChoiceField(
                    widget=forms.Select(attrs={'div_class': element.width}), choices=choices,
                    required=element.required if fields_required else False)
            elif element.kind == 'email':
                self.fields[str(element.pk)] = forms.EmailField(
                    widget=forms.TextInput(attrs={'div_class': element.width}),
                    required=element.required if fields_required else False)
            elif element.kind == 'check':
                self.fields[str(element.pk)] = forms.BooleanField(
                    widget=forms.CheckboxInput(attrs={'is_checkbox': True}),
                    required=element.required if fields_required else False)

            self.fields[str(element.pk)].help_text = element.help_text
            self.fields[str(element.pk)].label = element.name

            if answer:
                self.fields[str(element.pk)].initial = answer.edited_answer if answer.edited_answer else answer.answer

            if review_assignment:
                answers = review_assignment.review_form_answers()
                if answers:
                    try:
                        answer = answers.get(original_element=element)
                        self.fields[str(element.pk)].initial = answer.answer
                    except (models.ReviewFormAnswer.DoesNotExist, models.ReviewAssignmentAnswer.DoesNotExist):
                        pass


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


class ReviewVisibilityForm(forms.ModelForm):
    class Meta:
        model = models.ReviewAssignment
        fields = ('for_author_consumption', 'display_review_file')
        labels = {
            "for_author_consumption": _("Author can access this review"),
            "display_review_file": _("Author can access review file"),
        }
        widgets = {
            "for_author_consumption": HTMLSwitchInput(),
            "display_review_file": HTMLSwitchInput(),
        }

    def __init__(self, *args, **kwargs):
        super(ReviewVisibilityForm, self).__init__(*args, **kwargs)
        if not self.instance.review_file:
            self.fields.pop('display_review_file')


class AnswerVisibilityForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.review_assignment = kwargs.pop('review_assignment', None)
        super(AnswerVisibilityForm, self).__init__(*args, **kwargs)

        for answer in self.review_assignment.review_form_answers():
            label = _("Author can see ‘%(name)s’") % {'name': answer.best_label}
            self.fields[str(answer.pk)] = forms.BooleanField(
                label=label,
                widget=HTMLSwitchInput(),
                required=False,
                initial=True if answer.author_can_see else False,
            )

    def save(self, commit=True):
        for answer_id, visibility in self.cleaned_data.items():
            answer = self.review_assignment.review_form_answers().get(
                pk=answer_id,
            )
            answer.author_can_see = visibility
            if commit:
                answer.save()

        return self.review_assignment.review_form_answers()

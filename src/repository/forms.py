from django import forms
from django.forms import modelformset_factory
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget

from submission import models as submission_models
from repository import models
from press import models as press_models
from review.forms import render_choices


class PreprintInfo(forms.ModelForm):
    keywords = forms.CharField(required=False)
    subject = forms.ModelChoiceField(
        required=True,
        queryset=models.Subject.objects.none(),
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = models.Preprint
        fields = (
            'title',
            'abstract',
            'license',
            'comments_editor',
            'subject',
        )
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Title')}),
            'abstract': forms.Textarea(
                attrs={
                    'placeholder': _('Enter your article\'s abstract here')
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        elements = self.request.repository.additional_submission_fields()
        super(PreprintInfo, self).__init__(*args, **kwargs)

        self.fields['subject'].queryset = models.Subject.objects.filter(
            enabled=True,
            repository=self.request.repository,
        )
        self.fields['license'].queryset = submission_models.Licence.objects.filter(
            press__isnull=False,
            available_for_submission=True,
        )
        self.fields['license'].required = True

        if elements:
            for element in elements:
                if element.input_type == 'text':
                    self.fields[element.name] = forms.CharField(
                        widget=forms.TextInput(),
                        required=element.required)
                elif element.input_type == 'textarea':
                    self.fields[element.name] = forms.CharField(
                        widget=forms.Textarea,
                        required=element.required,
                    )
                elif element.input_type == 'date':
                    self.fields[element.name] = forms.CharField(
                        widget=forms.DateInput(
                            attrs={
                                'class': 'datepicker',
                            }
                        ),
                        required=element.required)

                elif element.input_type == 'select':
                    choices = render_choices(element.choices)
                    self.fields[element.name] = forms.ChoiceField(
                        widget=forms.Select(),
                        choices=choices,
                        required=element.required,
                    )

                elif element.input_type == 'email':
                    self.fields[element.name] = forms.EmailField(
                        widget=forms.TextInput(),
                        required=element.required,
                    )
                elif element.input_type == 'check':
                    self.fields[element.name] = forms.BooleanField(
                        widget=forms.CheckboxInput(attrs={'is_checkbox': True}),
                        required=element.required)

                self.fields[element.name].help_text = element.help_text
                self.fields[element.name].label = element.name

                preprint = kwargs['instance']
                if preprint:
                    try:
                        check_for_answer = models.RepositoryFieldAnswer.objects.get(
                            field=element,
                            preprint=preprint,
                        )
                        self.fields[element.name].initial = check_for_answer.answer
                    except submission_models.FieldAnswer.DoesNotExist:
                        pass

    def save(self, commit=True):
        preprint = super(PreprintInfo, self).save()

        preprint.owner = self.request.user
        preprint.repository = self.request.repository

        posted_keywords = self.cleaned_data['keywords'].split(',')
        for keyword in posted_keywords:
            new_keyword, c = submission_models.Keyword.objects.get_or_create(word=keyword)
            preprint.keywords.add(new_keyword)

        for keyword in preprint.keywords.all():
            if keyword.word not in posted_keywords:
                preprint.keywords.remove(keyword)

        if self.request:
            additional_fields = models.RepositoryField.objects.filter(
                repository=self.request.repository,
            )
            for field in additional_fields:
                answer = self.request.POST.get(field.name, None)

                if answer:
                    try:
                        field_answer = models.RepositoryFieldAnswer.objects.get(
                            preprint=preprint,
                            field=field,
                        )
                        field_answer.answer = answer
                        field_answer.save()
                    except models.RepositoryFieldAnswer.DoesNotExist:
                        models.RepositoryFieldAnswer.objects.create(
                            preprint=preprint,
                            field=field,
                            answer=answer,
                        )

        if commit:
            preprint.save()

        return preprint


class AuthorForm(forms.ModelForm):
    class Meta:
        model = models.Author
        fields = (
            'email_address',
            'first_name',
            'middle_name',
            'last_name',
            'affiliation',
            'orcid',
        )


AuthorFormSet = modelformset_factory(
    models.Author,
    fields=(
        'email_address',
        'first_name',
        'middle_name',
        'last_name',
        'affiliation',
        'orcid',
    )
)


class CommentForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ('body',)


class SettingsForm(forms.ModelForm):
    class Meta:
        model = press_models.Press
        fields = (
            'preprints_about',
            'preprint_start',
            'preprint_submission',
            'preprint_publication',
            'preprint_decline',
            'preprint_pdf_only',
        )
        widgets = {
            'preprints_about': SummernoteWidget,
            'preprint_start': SummernoteWidget,
            'preprint_submission': SummernoteWidget,
            'preprint_publication': SummernoteWidget,
            'preprint_decline': SummernoteWidget,
        }

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            press = kwargs['instance']
            settings = press_models.PressSetting.objects.filter(press=press)

            for setting in settings:
                if setting.is_boolean:
                    self.fields[setting.name] = forms.BooleanField(
                        widget=forms.CheckboxInput(),
                        required=False,
                    )
                else:
                    self.fields[setting.name] = forms.CharField(
                        widget=forms.TextInput(),
                        required=False,
                    )
                self.fields[setting.name].initial = setting.value

    def save(self, commit=True):
        press = super(SettingsForm, self).save()
        settings = press_models.PressSetting.objects.filter(press=press)

        for setting in settings:
            if setting.is_boolean:
                setting.value = 'On' if self.cleaned_data[setting.name] else ''
            else:
                setting.value = self.cleaned_data[setting.name]
            setting.save()


class SubjectForm(forms.ModelForm):
    class Meta:
        model = models.Subject
        exclude = ('preprints',)


class FileForm(forms.ModelForm):
    class Meta:
        model = models.PreprintFile
        fields = ('file',)

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop('preprint')
        super(FileForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        file = super(FileForm, self).save(commit=False)
        file.preprint = self.preprint

        if commit:
            file.save()

        return file

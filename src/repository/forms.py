from django import forms
from django.forms import modelformset_factory
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.text import slugify

from submission import models as submission_models
from repository import models
from press import models as press_models
from review.forms import render_choices


class PreprintInfo(forms.ModelForm):
    submission_agreement = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=True,
    )
    keywords = forms.CharField(required=False)
    subject = forms.ModelMultipleChoiceField(
        required=True,
        queryset=models.Subject.objects.none(),
        widget=forms.SelectMultiple(attrs={'multiple': ''}),
    )

    class Meta:
        model = models.Preprint
        fields = (
            'title',
            'abstract',
            'license',
            'comments_editor',
            'subject',
            'doi',
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
        self.admin = kwargs.pop('admin', False)
        elements = self.request.repository.additional_submission_fields()
        super(PreprintInfo, self).__init__(*args, **kwargs)
        print(self.admin)
        if self.admin:
            self.fields.pop('submission_agreement')
            self.fields.pop('comments_editor')

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
                elif element.input_type == 'number':
                    self.fields[element.name] = forms.IntegerField(
                        required=element.required,
                    )
                else:
                    self.fields[element.name] = forms.TextInput()

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
                    except models.RepositoryFieldAnswer.DoesNotExist:
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


class PreprintSupplementaryFileForm(forms.ModelForm):
    class Meta:
        model = models.PreprintSupplementaryFile
        fields = ( 'label', 'url',)

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop('preprint')
        super(PreprintSupplementaryFileForm, self).__init__(*args, **kwargs)


    def save(self, commit=True):
        link = super(PreprintSupplementaryFileForm, self).save(commit=False)
        link.preprint = self.preprint

        if commit:
            link.save()

        return link




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

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop('preprint', None)
        self.author = kwargs.pop('author', None)
        super(CommentForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        comment = super(CommentForm, self).save(commit=False)
        comment.preprint = self.preprint
        comment.author = self.author

        if commit:
            comment.save()

        return comment


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
        exclude = ('repository', 'slug')

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop('repository')
        super(SubjectForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        subject = super(SubjectForm, self).save(commit=False)
        subject.repository = self.repository
        subject.slug = slugify(subject.name)

        if commit:
            subject.save()

        return subject


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
            file.mime_type = file.get_file_mime_type()
            file.size = file.file.size
            file.save()

        return file


class VersionForm(forms.ModelForm):
    class Meta:
        model = models.VersionQueue
        fields = ('update_type', 'title', 'abstract')

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop('preprint')
        super(VersionForm, self).__init__(*args, **kwargs)
        self.fields['title'].initial = self.preprint.title
        self.fields['abstract'].initial = self.preprint.abstract

    def save(self, commit=True):
        version = super(VersionForm, self).save(commit=False)
        version.preprint = self.preprint

        if commit:
            version.save()

        return version


class RepositoryBase(forms.ModelForm):
    class Meta:
        model = models.Repository
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.press = kwargs.pop('press')
        super(RepositoryBase, self).__init__(*args, **kwargs)


class RepositoryInitial(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = (
            'name',
            'short_name',
            'domain',
            'object_name',
            'object_name_plural',
            'publisher',
        )

    def __init__(self, *args, **kwargs):
        super(RepositoryInitial, self).__init__(*args, **kwargs)

        if settings.URL_CONFIG == 'path':
            del(self.fields['domain'])

    def save(self, commit=True):
        repository = super(RepositoryInitial, self).save(commit=False)
        repository.press = self.press

        if settings.URL_CONFIG:
            repository.domain = '{short_name}.domain.com'.format(
                short_name=repository.short_name,
            )

        if commit:
            repository.save()

        return repository


class RepositorySite(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = (
            'about',
            'logo',
            'hero_background',
            'favicon',
            'footer',
            'login_text',
            'custom_js_code',
        )
        widgets = {
            'about': SummernoteWidget,
            'footer': SummernoteWidget,
            'login_text': SummernoteWidget,
        }


class RepositorySubmission(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = (
            'start',
            'submission_agreement',
            'limit_upload_to_pdf',
            'managers',
        )

        widgets = {
            'start': SummernoteWidget,
            'submission_agreement': SummernoteWidget,
            'managers': FilteredSelectMultiple(
                "Accounts",
                False,
                attrs={'rows': '2'},
            )
        }


class RepositoryEmails(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = (
            'submission',
            'publication',
            'decline',
            'accept_version',
            'decline_version',
            'new_comment',
        )

        widgets = {
            'submission': SummernoteWidget,
            'publication': SummernoteWidget,
            'decline': SummernoteWidget,
            'accept_version': SummernoteWidget,
            'decline_version': SummernoteWidget,
            'new_comment': SummernoteWidget,
        }


class RepositoryLiveForm(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = (
            'live',
        )


class RepositoryFieldForm(forms.ModelForm):
    class Meta:
        model = models.RepositoryField
        fields = (
            'name',
            'input_type',
            'choices',
            'required',
            'order',
            'help_text',
            'display',
            'dc_metadata_type',
        )

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop('repository')
        super(RepositoryFieldForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        field = super(RepositoryFieldForm, self).save(commit=False)
        field.repository = self.repository

        if commit:
            field.save()

        return field

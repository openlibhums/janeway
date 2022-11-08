from django import forms
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.text import slugify
from django.contrib import messages

from submission import models as submission_models
from repository import models
from press import models as press_models
from review.logic import render_choices
from core import models as core_models, workflow
from utils import forms as utils_forms
from identifiers.models import URL_DOI_RE
from core.widgets import TableMultiSelectUser


class PreprintInfo(utils_forms.KeywordModelForm):
    submission_agreement = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=True,
    )
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
        if self.admin:
            self.fields.pop('submission_agreement')
            self.fields.pop('comments_editor')

        self.fields['subject'].queryset = models.Subject.objects.filter(
            enabled=True,
            repository=self.request.repository,
        )
        if self.admin:
            self.fields['license'].queryset = submission_models.Licence.objects.filter(
                journal__isnull=True,
            )
        else:
            self.fields['license'].queryset = self.request.repository.active_licenses.all()
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
                elif element.input_type == 'checkbox':
                    self.fields[element.name] = forms.BooleanField(
                        widget=forms.CheckboxInput(attrs={'is_checkbox': True}),
                        required=element.required)
                elif element.input_type == 'number':
                    self.fields[element.name] = forms.IntegerField(
                        required=element.required,
                    )
                else:
                    self.fields[element.name] = forms.CharField(
                        widget=forms.Textarea(),
                        required=element.required,
                    )

                if element.input_type == 'date':
                    self.fields[element.name].help_text = 'Use ISO 8601 Date Format YYYY-MM-DD. {}'.format(element.help_text)
                else:
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

        # We only set the preprint owner once on creation.
        if not preprint.owner:
            preprint.owner = self.request.user

        preprint.repository = self.request.repository

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

    def clean_doi(self):
        doi_string = self.cleaned_data.get('doi')

        if doi_string and not URL_DOI_RE.match(doi_string):
            self.add_error(
                'doi',
                'DOIs should be in the following format: https://doi.org/10.XXX/XXXXX'
            )

        return doi_string


class PreprintSupplementaryFileForm(forms.ModelForm):
    class Meta:
        model = models.PreprintSupplementaryFile
        fields = ('label', 'url',)

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop('preprint')
        super(PreprintSupplementaryFileForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        link = super(PreprintSupplementaryFileForm, self).save(commit=False)
        link.preprint = self.preprint

        if commit:
            link.save()

        return link


class AuthorForm(forms.Form):
    email_address = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=200)
    middle_name = forms.CharField(max_length=200, required=False)
    last_name = forms.CharField(max_length=200)
    affiliation = forms.CharField(max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        self.request = kwargs.pop('request')
        self.preprint = kwargs.pop('preprint')
        super(AuthorForm, self).__init__(*args, **kwargs)

        if self.instance:
            self.fields['email_address'].initial = self.instance.account.email
            self.fields['first_name'].initial = self.instance.account.first_name
            self.fields['middle_name'].initial = self.instance.account.middle_name
            self.fields['last_name'].initial = self.instance.account.last_name
            self.fields['affiliation'].initial = self.instance.affiliation or self.instance.account.institution

    def save(self):
        cleaned_data = self.cleaned_data
        if self.instance:
            account = self.instance.account
            account.email = cleaned_data.get('email_address')
            account.first_name = cleaned_data.get('first_name')
            account.middle_name = cleaned_data.get('middle_name')
            account.last_name = cleaned_data.get('last_name')
            self.instance.affiliation = cleaned_data.get('affiliation')

            account.save()
            self.instance.save()
            return self.instance
        else:
            account, ac = core_models.Account.objects.get_or_create(
                email=cleaned_data.get('email_address'),
                defaults={
                    'first_name': cleaned_data.get('first_name'),
                    'middle_name': cleaned_data.get('middle_name'),
                    'last_name': cleaned_data.get('last_name'),
                }
            )
            preprint_author, pc = models.PreprintAuthor.objects.get_or_create(
                account=account,
                preprint=self.preprint,
                defaults={
                    'affiliation': cleaned_data.get('affiliation'),
                    'order': self.preprint.next_author_order()
                }
            )

            if not ac:
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    'A user with this email address was found. They have been added.'
                )
            else:
                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    'User added as Author.',
                )

            return preprint_author


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
        self.fields['parent'].queryset = models.Subject.objects.filter(
            repository=self.repository,
        )

    def save(self, commit=True):
        subject = super(SubjectForm, self).save(commit=False)
        subject.repository = self.repository
        subject.slug = slugify(subject.name)

        if commit:
            subject.save()

        return subject


class ActiveLicenseForm(forms.ModelForm):
    class Meta:
        model = models.Repository
        fields = ('active_licenses',)
        widgets = {
            'active_licenses': forms.CheckboxSelectMultiple,
        }
        labels = {
            'active_licenses': 'Select the licenses that authors can pick from during submission',
        }

    def __init__(self, *args, **kwargs):
        super(ActiveLicenseForm, self).__init__(*args, **kwargs)
        self.fields['active_licenses'].queryset = submission_models.Licence.objects.filter(
            journal=None
        )
        self.fields['active_licenses'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        return obj.name


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
        fields = ('title', 'abstract', 'published_doi')

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop('preprint')
        super(VersionForm, self).__init__(*args, **kwargs)
        self.fields['title'].initial = self.preprint.title
        self.fields['abstract'].initial = self.preprint.abstract
        self.fields['published_doi'].initial = self.preprint.doi

    def save(self, commit=True):
        version = super(VersionForm, self).save(commit=False)
        version.preprint = self.preprint

        if commit:
            version.save()

        return version

    def clean_published_doi(self):
        doi_string = self.cleaned_data.get('published_doi')

        if doi_string and not URL_DOI_RE.match(doi_string):
            self.add_error(
                'published_doi',
                'DOIs should be in the following format: https://doi.org/10.XXX/XXXXX'
            )

        return doi_string


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
        help_texts = {
            'domain': 'Using a custom domain requires configuring DNS. '
                'The repository will always be available under the /code path',
        }

    def save(self, commit=True):
        repository = super(RepositoryInitial, self).save(commit=False)
        repository.press = self.press

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
            'limit_access_to_submission',
            'submission_access_request_text',
            'submission_access_contact',
            'custom_js_code',
            'review_helper',
        )
        widgets = {
            'about': SummernoteWidget,
            'footer': SummernoteWidget,
            'login_text': SummernoteWidget,
            'submission_access_request_text': SummernoteWidget,
            'review_helper': SummernoteWidget,
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
            'review_invitation',
            'manager_review_status_change',
            'reviewer_review_status_change',
            'submission_notification_recipients',
        )

        widgets = {
            'submission': SummernoteWidget,
            'publication': SummernoteWidget,
            'decline': SummernoteWidget,
            'accept_version': SummernoteWidget,
            'decline_version': SummernoteWidget,
            'new_comment': SummernoteWidget,
            'review_invitation': SummernoteWidget,
            'manager_review_status_change': SummernoteWidget,
            'reviewer_review_status_change': SummernoteWidget,
            'submission_notification_recipients': TableMultiSelectUser()
        }

    def __init__(self, *args, **kwargs):
        super(RepositoryEmails, self).__init__(*args, **kwargs)
        repo_managers = kwargs['instance'].managers.all()
        self.fields['submission_notification_recipients'].queryset = repo_managers
        self.fields['submission_notification_recipients'].choices = [(m.id, {"name": m.full_name(), "email": m.email}) for m in repo_managers]

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


class PreprinttoArticleForm(forms.Form):
    license = forms.ModelChoiceField(queryset=submission_models.Licence.objects.none())
    section = forms.ModelChoiceField(queryset=submission_models.Section.objects.none())
    stage = forms.ChoiceField(
        choices=()
    )
    force = forms.BooleanField(
        required=False,
        help_text='If you want to force the creation of a new article object even if one exists, check this box. '
                  'The old article will be orphaned and no longer linked to this object.',
    )

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal', None)
        super(PreprinttoArticleForm, self).__init__(*args, **kwargs)

        if self.journal:
            self.fields['license'].queryset = submission_models.Licence.objects.filter(
                journal=self.journal,
            )
            self.fields['section'].queryset = submission_models.Section.objects.filter(
                journal=self.journal,
            )
            self.fields['stage'].choices = workflow.workflow_journal_choices(self.journal)


class ReviewForm(forms.ModelForm):
    class Meta:
        model = models.Review
        fields = (
            'reviewer',
            'date_due',
        )
        widgets = {
            'date_due': utils_forms.HTMLDateInput(),
        }

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop('preprint')
        self.manager = kwargs.pop('manager')
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.fields['reviewer'].queryset = self.preprint.repository.reviewer_accounts()

    def save(self, commit=True):
        review = super(ReviewForm, self).save(commit=False)
        review.preprint = self.preprint
        review.manager = self.manager
        review.status = 'new'

        if commit:
            review.save()

        return review


class ReviewDueDateForm(forms.ModelForm):
    class Meta:
        model = models.Review
        fields = ('date_due',)
        widgets = {
            'date_due': utils_forms.HTMLDateInput(),
        }


class ReviewCommentForm(forms.Form):
    body = forms.CharField(
        widget=SummernoteWidget(),
        label="Comments",
    )
    anonymous = forms.BooleanField(
        help_text='Check if you want your comments to be displayed anonymously.',
        label="Comment Anonymously",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.review = kwargs.pop('review')
        super(ReviewCommentForm, self).__init__(*args, **kwargs)
        if self.review.comment:
            self.fields['body'].initial = self.review.comment.body
            self.fields['anonymous'].initial = self.review.anonymous

    def save(self):
        if self.cleaned_data:
            if self.review.comment:
                comment = self.review.comment
            else:
                comment = models.Comment()

            comment.author = self.review.reviewer
            comment.preprint = self.review.preprint
            comment.body = self.cleaned_data.get('body')
            comment.save()

            self.review.anonymous = self.cleaned_data.get('anonymous', False)
            self.review.comment = comment
            self.review.save()


class ReviewForm(forms.ModelForm):
    class Meta:
        model = models.Review
        fields = (
            'reviewer',
            'date_due',
        )
        widgets = {
            'date_due': utils_forms.HTMLDateInput(),
        }

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop('preprint')
        self.manager = kwargs.pop('manager')
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.fields['reviewer'].queryset = self.preprint.repository.reviewer_accounts()

    def save(self, commit=True):
        review = super(ReviewForm, self).save(commit=False)
        review.preprint = self.preprint
        review.manager = self.manager
        review.status = 'new'

        if commit:
            review.save()

        return review


class ReviewDueDateForm(forms.ModelForm):
    class Meta:
        model = models.Review
        fields = ('date_due',)
        widgets = {
            'date_due': utils_forms.HTMLDateInput(),
        }


class ReviewCommentForm(forms.Form):
    body = forms.CharField(
        widget=SummernoteWidget(),
        label="Comments",
    )
    anonymous = forms.BooleanField(
        help_text='Check if you want your comments to be displayed anonymously.',
        label="Comment Anonymously",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.review = kwargs.pop('review')
        super(ReviewCommentForm, self).__init__(*args, **kwargs)
        if self.review.comment:
            self.fields['body'].initial = self.review.comment.body
            self.fields['anonymous'].initial = self.review.anonymous

    def save(self):
        if self.cleaned_data:
            if self.review.comment:
                comment = self.review.comment
            else:
                comment = models.Comment()

            comment.author = self.review.reviewer
            comment.preprint = self.review.preprint
            comment.body = self.cleaned_data.get('body')
            comment.save()

            self.review.anonymous = self.cleaned_data.get('anonymous', False)
            self.review.comment = comment
            self.review.save()

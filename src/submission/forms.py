__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import re

from django import forms
from django.utils.translation import gettext, gettext_lazy as _

from submission import models
from core import models as core_models
from identifiers import models as ident_models
from journal import models as journal_models
from review.logic import render_choices
from utils.forms import (
    KeywordModelForm,
    JanewayTranslationModelForm,
    HTMLDateInput,
)
from utils import setting_handler

from tinymce.widgets import TinyMCE


class PublisherNoteForm(forms.ModelForm):

    class Meta:
        model = models.PublisherNote
        fields = ('text',)


class ArticleStart(forms.ModelForm):

    class Meta:
        model = models.Article
        fields = ('publication_fees', 'submission_requirements', 'copyright_notice',
                  'competing_interests')

    def __init__(self, *args, **kwargs):
        journal = kwargs.pop('journal', False)
        super(ArticleStart, self).__init__(*args, **kwargs)

        self.fields['competing_interests'].label = ''

        if not journal.submissionconfiguration.publication_fees:
            self.fields.pop('publication_fees')
        else:
            self.fields['publication_fees'].required = True

        if not journal.submissionconfiguration.submission_check:
            self.fields.pop('submission_requirements')
        else:
            self.fields['submission_requirements'].required = True

        if not journal.submissionconfiguration.copyright_notice:
            self.fields.pop('copyright_notice')
        else:
            self.fields['copyright_notice'].required = True
            copyright_label = setting_handler.get_setting(
                'general',
                'copyright_submission_label',
                journal,
            ).processed_value
            self.fields['copyright_notice'].label = copyright_label

        if not journal.submissionconfiguration.competing_interests:
            self.fields.pop('competing_interests')


class SelectIssueForm(forms.ModelForm):
    """Used to choose the destination special issue during submission."""

    primary_issue = forms.ModelChoiceField(
        queryset=None,
        required=False,
        blank=True,
        empty_label=gettext("No selection"),
        widget=forms.RadioSelect(),
    )

    class Meta:
        model = models.Article
        fields = ("primary_issue",)

    def __init__(self, *args, **kwargs):
        """Init the query set now, otherwise we are missing a current_journal."""
        journal = kwargs.pop('journal', False)
        user = kwargs.pop('user', False)
        super().__init__(*args, **kwargs)
        self.fields["primary_issue"].queryset = (
            journal_models.Issue.objects.by_user(user).open_for_submission().current_journal(journal)
        )


class ArticleInfo(KeywordModelForm, JanewayTranslationModelForm):
    FILTER_PUBLIC_FIELDS = False

    class Meta:
        model = models.Article
        fields = (
            'title', 'subtitle', 'abstract', 'non_specialist_summary',
            'language', 'section', 'license', 'primary_issue',
            'article_number', 'is_remote', 'remote_url', 'peer_reviewed',
            'first_page', 'last_page', 'page_numbers', 'total_pages',
            'competing_interests', 'custom_how_to_cite', 'rights',
        )
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Title')}),
            'subtitle': forms.TextInput(attrs={'placeholder': _('Subtitle')}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialises the ArticleInfo form.
        :param kwargs:  elements: queryest of Field objects.
                        submission_sumary: boolean, detmines if this field
                        is on or off.
                        journal: Journal object.
                        pop_disabled_fields: boolean, if False we do not pop
                        fields that are disabled by SubmissionConfiguration
                        or overwrite their saving.
        """
        elements = kwargs.pop('additional_fields', None)
        submission_summary = kwargs.pop('submission_summary', None)
        journal = kwargs.pop('journal', None)
        self.keep_primary_issue = kwargs.pop('keep_primary_issue', False)
        self.pop_disabled_fields = kwargs.pop('pop_disabled_fields', True)
        editor_view = kwargs.pop('editor_view', False)
        super(ArticleInfo, self).__init__(*args, **kwargs)

        # Flag labels for translation
        for field in self.fields.values():
            field.label = _(field.label)

        if 'instance' in kwargs:
            article = kwargs['instance']
            section_queryset = models.Section.objects.filter(
                journal=article.journal,
            )
            license_queryset = models.Licence.objects.filter(
                journal=article.journal,
            )
            if self.FILTER_PUBLIC_FIELDS:
                section_queryset = section_queryset.filter(
                    public_submissions=self.FILTER_PUBLIC_FIELDS,
                )
                license_queryset = license_queryset.filter(
                    available_for_submission=self.FILTER_PUBLIC_FIELDS,
                )
            if article.primary_issue and article.primary_issue.allowed_sections:
                section_queryset = section_queryset.filter(
                    pk__in=article.primary_issue.allowed_sections.values_list('pk', flat=True),
                )
            self.fields['section'].queryset = section_queryset
            self.fields['license'].queryset = license_queryset

            self.fields['section'].required = True
            self.fields['license'].required = True
            self.fields['primary_issue'].queryset = article.issues.all()

            abstracts_required = article.journal.get_setting(
                'general',
                'abstract_required',
            )

            if abstracts_required:
                self.fields['abstract'].required = True

            if submission_summary:
                self.fields['non_specialist_summary'].required = True

            # Pop fields based on journal.submissionconfiguration
            if journal and self.pop_disabled_fields:
                if not journal.submissionconfiguration.subtitle:
                    self.fields.pop('subtitle')

                if not journal.submissionconfiguration.abstract:
                    self.fields.pop('abstract')

                if not journal.submissionconfiguration.language:
                    self.fields.pop('language')

                if not journal.submissionconfiguration.license:
                    self.fields.pop('license')

                if not journal.submissionconfiguration.keywords:
                    self.fields.pop('keywords')

                if not journal.submissionconfiguration.section:
                    self.fields.pop('section')

            # Add additional fields
            if elements:
                for element in elements:
                    if element.kind == 'text':
                        self.fields[element.name] = forms.CharField(
                            widget=forms.TextInput(attrs={'div_class': element.width}),
                            required=element.required)
                    elif element.kind == 'textarea':
                        self.fields[element.name] = forms.CharField(
                                widget=TinyMCE(),
                                required=element.required,
                        )
                    elif element.kind == 'date':
                        self.fields[element.name] = forms.CharField(
                            widget=HTMLDateInput(
                                attrs={'div_class': element.width},
                            ),
                            required=element.required)

                    elif element.kind == 'select':
                        choices = render_choices(element.choices)
                        self.fields[element.name] = forms.ChoiceField(
                            widget=forms.Select(attrs={'div_class': element.width}), choices=choices,
                            required=element.required)

                    elif element.kind == 'email':
                        self.fields[element.name] = forms.EmailField(
                            widget=forms.TextInput(attrs={'div_class': element.width}),
                            required=element.required)
                    elif element.kind == 'check':
                        self.fields[element.name] = forms.BooleanField(
                            widget=forms.CheckboxInput(attrs={'is_checkbox': True}),
                            required=element.required)

                    self.fields[element.name].help_text = element.help_text
                    self.fields[element.name].label = element.name

                    if article:
                        try:
                            check_for_answer = models.FieldAnswer.objects.get(field=element, article=article)
                            self.fields[element.name].initial = check_for_answer.answer
                        except models.FieldAnswer.DoesNotExist:
                            pass

                    # if the editor is viewing the page, don't set additional
                    # fields to be required.
                    if editor_view:
                        self.fields[element.name].required = False

    def clean(self):
        cleaned_data = super().clean()
        if self.keep_primary_issue:
            cleaned_data['primary_issue'] = self.instance.primary_issue
        return cleaned_data

    def save(self, commit=True, request=None):
        article = super(ArticleInfo, self).save(commit=False)

        if request:
            additional_fields = models.Field.objects.filter(journal=request.journal)

            for field in additional_fields:
                answer = request.POST.get(field.name, None)
                if answer:
                    try:
                        field_answer = models.FieldAnswer.objects.get(article=article, field=field)
                        field_answer.answer = answer
                        field_answer.save()
                    except models.FieldAnswer.DoesNotExist:
                        field_answer = models.FieldAnswer.objects.create(article=article, field=field, answer=answer)

            if self.pop_disabled_fields:
                request.journal.submissionconfiguration.handle_defaults(article)

        if commit:
            article.save()

        return article


class ArticleInfoSubmit(ArticleInfo):
    # Filter licenses and sections to publicly available only
    FILTER_PUBLIC_FIELDS = True


class EditorArticleInfoSubmit(ArticleInfo):
    # Used when an editor is making a submission.
    FILTER_PUBLIC_FIELDS = False

    def __init__(self, *args, **kwargs):
        super(EditorArticleInfoSubmit, self).__init__(*args, **kwargs)
        if self.fields.get('section'):
            self.fields['section'].label_from_instance = lambda obj: obj.display_name_public_submission
            self.fields['section'].help_text = "As an editor you will see all " \
                                               "sections even if they are  " \
                                               "closed for public submission"


class AuthorForm(forms.ModelForm):

    class Meta:
        model = core_models.Account
        exclude = (
            'date_joined',
            'activation_code'
            'date_confirmed'
            'confirmation_code'
            'reset_code'
            'reset_code_validated'
            'roles'
            'interest'
            'is_active'
            'is_staff'
            'is_admin'
            'password',
            'username',
            'roles',
        )

        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'middle_name': forms.TextInput(attrs={'placeholder': _('Middle name')}),
            'last_name': forms.TextInput(attrs={'placeholder': _('Last name')}),
            'biography': forms.Textarea(
                attrs={'placeholder': _('Enter biography here')}),
            'institution': forms.TextInput(attrs={'placeholder': _('Institution')}),
            'department': forms.TextInput(attrs={'placeholder': _('Department')}),
            'twitter': forms.TextInput(attrs={'placeholder': _('Twitter handle')}),
            'linkedin': forms.TextInput(attrs={'placeholder': _('LinkedIn profile')}),
            'impactstory': forms.TextInput(attrs={'placeholder': _('ImpactStory profile')}),
            'orcid': forms.TextInput(attrs={'placeholder': _('ORCID ID')}),
            'email': forms.TextInput(attrs={'placeholder': _('Email address')}),
        }

    def __init__(self, *args, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)
        self.fields['password'].required = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_orcid(self):
        orcid_string = self.cleaned_data.get('orcid')
        try:
            return utility_clean_orcid(orcid_string)
        except ValueError:
            self.add_error(
                'orcid',
                 'An ORCID must be entered in the pattern '
                'https://orcid.org/0000-0000-0000-0000 or'
                ' 0000-0000-0000-0000. You can find out '
                'about valid ORCID patterns on the ORCID support site: '
                'https://support.orcid.org/hc/en-us/articles/'
                '360006897674-Structure-of-the-ORCID-Identifier',
            )
        return orcid_string


class SubmissionCommentsForm(forms.ModelForm):
    class Meta:
        model = models.Article
        fields = ('comments_editor',)
        labels = {
            'comments_editor': '',
        }


class FileDetails(forms.ModelForm):

    class Meta:
        model = core_models.File
        fields = (
            'label',
            'description',
        )

    def __init__(self, *args, **kwargs):
        super(FileDetails, self).__init__(*args, **kwargs)
        self.fields['label'].required = True
        self.fields['label'].inital = 'Manuscript'


class EditFrozenAuthor(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.pop("instance", None)
        if instance:
            if instance.author:
                self.fields["frozen_email"].help_text += gettext(
                    "Currently linked to %s, leave blank to use this address"
                    "" % instance.author.email,
                )
                if instance.author.orcid:
                    self.fields["frozen_orcid"].help_text += gettext(
                        "If left blank, the account ORCiD will be used (%s)"
                        "" % instance.author.orcid,
                    )
            del self.fields["is_corporate"]
            if instance.is_corporate:
                del self.fields["name_prefix"]
                del self.fields["first_name"]
                del self.fields["middle_name"]
                del self.fields["last_name"]
                del self.fields["name_suffix"]

    class Meta:
        model = models.FrozenAuthor
        fields = (
            'name_prefix',
            'first_name',
            'middle_name',
            'last_name',
            'name_suffix',
            'institution',
            'department',
            'frozen_biography',
            'country',
            'is_corporate',
            'frozen_email',
            'frozen_orcid',
            'display_email',
        )

    def save(self, commit=True, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        if commit is True and obj.frozen_email:
            try:
                # Associate with account if one exists
                account = core_models.Account.objects.get(
                    username=obj.frozen_email.lower())
                obj.author = account
                obj.frozen_email = None
            except core_models.Account.DoesNotExist:
                pass
            obj.save()
        return obj

    def clean_frozen_orcid(self):
        orcid_string = self.cleaned_data.get('frozen_orcid')
        try:
            return utility_clean_orcid(orcid_string)
        except ValueError:
            self.add_error(
                'frozen_orcid',
                'An ORCID must be entered in the pattern '
                'https://orcid.org/0000-0000-0000-0000 or'
                ' 0000-0000-0000-0000. You can find out '
                'about valid ORCID patterns on the ORCID support site: '
                'https://support.orcid.org/hc/en-us/articles/'
                '360006897674-Structure-of-the-ORCID-Identifier',
            )
        return orcid_string


class IdentifierForm(forms.ModelForm):

    class Meta:
        model = ident_models.Identifier
        fields = (
            'id_type',
            'identifier',
            'enabled',
        )


class FieldForm(forms.ModelForm):

    class Meta:
        model = models.Field
        exclude = (
            'journal',
            'press',
        )


class LicenseForm(forms.ModelForm):

    class Meta:
        model = models.Licence
        exclude = (
            'journal',
            'press',
        )


class ConfiguratorForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ConfiguratorForm, self).__init__(*args, **kwargs)
        self.fields['default_section'].queryset = models.Section.objects.filter(
            journal=self.instance.journal,
        )
        self.fields[
            'default_license'].queryset = models.Licence.objects.filter(
            journal=self.instance.journal,
        )

    def clean(self):
        cleaned_data = super().clean()

        license = cleaned_data.get('license', False)
        section = cleaned_data.get('section', False)
        language = cleaned_data.get('language', False)

        default_license = cleaned_data.get('default_license', None)
        default_section = cleaned_data.get('default_section', None)
        default_language = cleaned_data.get('default_language', None)

        if not license and not default_license:
            self.add_error(
                'default_license',
                'If license is unset you must select a default license.',
            )

        if not section and not default_section:
            self.add_error(
                'default_section',
                'If section is unset you must select a default section.',
            )

        if not language and not default_language:
            self.add_error(
                'default_language',
                'If language is unset you must select a default language.'
            )

    class Meta:
        model = models.SubmissionConfiguration
        exclude = (
            'journal',
        )


class ProjectedIssueForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProjectedIssueForm, self).__init__(*args, **kwargs)
        self.fields['projected_issue'].queryset = self.instance.journal.issue_set.all()

    class Meta:
        model = models.Article
        fields = ('projected_issue',)


class ArticleFundingForm(forms.ModelForm):

    class Meta:
        model = models.ArticleFunding
        fields = ('name', 'fundref_id', 'funding_id', 'funding_statement')
        widgets = {
            'funding_statement': TinyMCE(),
        }

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True, *args, **kwargs):
        funder = super().save(commit=commit, *args, **kwargs)
        if self.article:
            funder.article = self.article
        if commit:
            funder.save()
        return funder


def utility_clean_orcid(orcid):
    """
    Utility function that cleans an ORCID ID.
    """
    if orcid:
        orcid_regex = re.compile('([0]{3})([0,9]{1})-([0-9]{4})-([0-9]{4})-([0-9]{3})([0-9X]{1})')
        result = orcid_regex.search(orcid)

        if result:
            return result.group(0)
        else:
            raise ValueError('ORCID is not valid.')

    # ORCID is None.
    return orcid


class PubDateForm(forms.ModelForm):
    class Meta:
        model = models.Article
        fields = ('date_published',)

    def save(self, commit=True):
        article = super().save(commit=commit)
        if commit:
            article.fixedpubcheckitems.set_pub_date = bool(
                article.date_published
            )
            article.fixedpubcheckitems.save()
            article.save()
        return article

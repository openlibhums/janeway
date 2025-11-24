__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import re
import warnings

from django import forms
from django.utils.translation import gettext, gettext_lazy as _

from submission import models
from core import models as core_models
from identifiers import models as ident_models
from review.logic import render_choices
from utils.forms import (
    KeywordModelForm,
    JanewayTranslationModelForm,
    HTMLDateInput,
    clean_orcid_id,
    YesNoRadio,
)
from utils import setting_handler

from tinymce.widgets import TinyMCE


class PublisherNoteForm(forms.ModelForm):
    class Meta:
        model = models.PublisherNote
        fields = ("text",)


class ArticleStart(forms.ModelForm):
    class Meta:
        model = models.Article
        fields = (
            "publication_fees",
            "submission_requirements",
            "copyright_notice",
            "competing_interests",
        )

    def __init__(self, *args, **kwargs):
        journal = kwargs.pop("journal", False)
        super(ArticleStart, self).__init__(*args, **kwargs)

        self.fields["competing_interests"].label = ""

        if not journal.submissionconfiguration.publication_fees:
            self.fields.pop("publication_fees")
        else:
            self.fields["publication_fees"].required = True

        if not journal.submissionconfiguration.submission_check:
            self.fields.pop("submission_requirements")
        else:
            self.fields["submission_requirements"].required = True

        if not journal.submissionconfiguration.copyright_notice:
            self.fields.pop("copyright_notice")
        else:
            self.fields["copyright_notice"].required = True
            copyright_label = setting_handler.get_setting(
                "general",
                "copyright_submission_label",
                journal,
            ).processed_value
            self.fields["copyright_notice"].label = copyright_label

        if not journal.submissionconfiguration.competing_interests:
            self.fields.pop("competing_interests")


class ArticleInfo(KeywordModelForm, JanewayTranslationModelForm):
    FILTER_PUBLIC_FIELDS = False

    class Meta:
        model = models.Article
        fields = (
            "title",
            "subtitle",
            "abstract",
            "non_specialist_summary",
            "language",
            "section",
            "license",
            "primary_issue",
            "article_number",
            "is_remote",
            "remote_url",
            "peer_reviewed",
            "first_page",
            "last_page",
            "page_numbers",
            "total_pages",
            "custom_how_to_cite",
            "rights",
        )
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": _("Title")}),
            "subtitle": forms.TextInput(attrs={"placeholder": _("Subtitle")}),
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
        elements = kwargs.pop("additional_fields", None)
        submission_summary = kwargs.pop("submission_summary", None)
        journal = kwargs.pop("journal", None)
        self.pop_disabled_fields = kwargs.pop("pop_disabled_fields", True)
        editor_view = kwargs.pop("editor_view", False)
        super(ArticleInfo, self).__init__(*args, **kwargs)

        # Flag labels for translation
        for field in self.fields.values():
            field.label = _(field.label)

        if "instance" in kwargs:
            article = kwargs["instance"]
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
            self.fields["section"].queryset = section_queryset
            self.fields["license"].queryset = license_queryset

            self.fields["section"].required = True
            self.fields["license"].required = True
            self.fields["primary_issue"].queryset = article.issues.all()

            abstracts_required = article.journal.get_setting(
                "general",
                "abstract_required",
            )

            if abstracts_required:
                self.fields["abstract"].required = True

            if submission_summary:
                self.fields["non_specialist_summary"].required = True

            # Pop fields based on journal.submissionconfiguration
            if journal and self.pop_disabled_fields:
                if not journal.submissionconfiguration.subtitle:
                    self.fields.pop("subtitle")

                if not journal.submissionconfiguration.abstract:
                    self.fields.pop("abstract")

                if not journal.submissionconfiguration.language:
                    self.fields.pop("language")

                if not journal.submissionconfiguration.license:
                    self.fields.pop("license")

                if not journal.submissionconfiguration.keywords:
                    self.fields.pop("keywords")

                if not journal.submissionconfiguration.section:
                    self.fields.pop("section")

            # Add additional fields
            if elements:
                for element in elements:
                    if element.kind == "text":
                        self.fields[element.name] = forms.CharField(
                            widget=forms.TextInput(attrs={"div_class": element.width}),
                            required=element.required,
                        )
                    elif element.kind == "textarea":
                        self.fields[element.name] = forms.CharField(
                            widget=TinyMCE(),
                            required=element.required,
                        )
                    elif element.kind == "date":
                        self.fields[element.name] = forms.CharField(
                            widget=HTMLDateInput(
                                attrs={"div_class": element.width},
                            ),
                            required=element.required,
                        )

                    elif element.kind == "select":
                        choices = render_choices(element.choices)
                        self.fields[element.name] = forms.ChoiceField(
                            widget=forms.Select(attrs={"div_class": element.width}),
                            choices=choices,
                            required=element.required,
                        )

                    elif element.kind == "email":
                        self.fields[element.name] = forms.EmailField(
                            widget=forms.TextInput(attrs={"div_class": element.width}),
                            required=element.required,
                        )
                    elif element.kind == "check":
                        self.fields[element.name] = forms.BooleanField(
                            widget=forms.CheckboxInput(attrs={"is_checkbox": True}),
                            required=element.required,
                        )

                    self.fields[element.name].help_text = element.help_text
                    self.fields[element.name].label = element.name

                    if article:
                        try:
                            check_for_answer = models.FieldAnswer.objects.get(
                                field=element, article=article
                            )
                            self.fields[element.name].initial = check_for_answer.answer
                        except models.FieldAnswer.DoesNotExist:
                            pass

                    # if the editor is viewing the page, don't set additional
                    # fields to be required.
                    if editor_view:
                        self.fields[element.name].required = False

    def save(self, commit=True, request=None):
        article = super(ArticleInfo, self).save(commit=False)

        if request:
            additional_fields = models.Field.objects.filter(journal=request.journal)

            for field in additional_fields:
                posted_value = request.POST.get(field.name)

                # Determine answer depending on field kind
                if field.kind == "check":
                    # Keep 'on' if checked otherwise store an empty string
                    answer = posted_value if posted_value is not None else ""
                else:
                    answer = posted_value

                # Checkbox type inputs should pass here so they are recorded
                if answer or field.kind == "check":
                    try:
                        field_answer = models.FieldAnswer.objects.get(
                            article=article,
                            field=field,
                        )
                        field_answer.answer = answer
                        field_answer.save()
                    except models.FieldAnswer.DoesNotExist:
                        models.FieldAnswer.objects.create(
                            article=article,
                            field=field,
                            answer=answer,
                        )

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
        if self.fields.get("section"):
            self.fields["section"].label_from_instance = (
                lambda obj: obj.display_name_public_submission
            )
            self.fields["section"].help_text = (
                "As an editor you will see all "
                "sections even if they are  "
                "closed for public submission"
            )


class EditArticleMetadata(ArticleInfo):
    class Meta(ArticleInfo.Meta):
        fields = ArticleInfo.Meta.fields + (
            "competing_interests",
            "jats_article_type_override",
        )


class AuthorForm(forms.ModelForm):
    """
    A barebones account form that authors can use to create
    accounts for their co-authors.
    """

    class Meta:
        model = core_models.Account
        fields = (
            "email",
            "name_prefix",
            "first_name",
            "middle_name",
            "last_name",
            "salutation",
            "suffix",
            "biography",
        )

    def __init__(self, *args, **kwargs):
        warnings.warn("Use frozen authors instead")
        super().__init__(*args, **kwargs)


class SubmissionCommentsForm(forms.ModelForm):
    class Meta:
        model = models.Article
        fields = ("comments_editor",)
        labels = {
            "comments_editor": "",
        }


class FileDetails(forms.ModelForm):
    class Meta:
        model = core_models.File
        fields = (
            "label",
            "description",
        )

    def __init__(self, *args, **kwargs):
        super(FileDetails, self).__init__(*args, **kwargs)
        self.fields["label"].required = True


class EditFrozenAuthor(forms.ModelForm):
    class Meta:
        model = models.FrozenAuthor
        fields = (
            "name_prefix",
            "first_name",
            "middle_name",
            "last_name",
            "name_suffix",
            "frozen_biography",
            "is_corporate",
            "frozen_email",
            "display_email",
        )
        widgets = {
            "is_corporate": YesNoRadio,
            "display_email": YesNoRadio,
        }

    def save(self, commit=True, *args, **kwargs):
        obj = super().save(commit=False, *args, **kwargs)
        if commit is True:
            obj.associate_with_account()
            obj.save()
        return obj


class IdentifierForm(forms.ModelForm):
    class Meta:
        model = ident_models.Identifier
        fields = (
            "id_type",
            "identifier",
            "enabled",
        )


class FieldForm(forms.ModelForm):
    class Meta:
        model = models.Field
        exclude = (
            "journal",
            "press",
        )


class LicenseForm(forms.ModelForm):
    class Meta:
        model = models.Licence
        exclude = (
            "journal",
            "press",
        )


class ConfiguratorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ConfiguratorForm, self).__init__(*args, **kwargs)
        self.fields["default_section"].queryset = models.Section.objects.filter(
            journal=self.instance.journal,
        )
        self.fields["default_license"].queryset = models.Licence.objects.filter(
            journal=self.instance.journal,
        )

    def clean(self):
        cleaned_data = super().clean()

        license = cleaned_data.get("license", False)
        section = cleaned_data.get("section", False)
        language = cleaned_data.get("language", False)

        default_license = cleaned_data.get("default_license", None)
        default_section = cleaned_data.get("default_section", None)
        default_language = cleaned_data.get("default_language", None)

        if not license and not default_license:
            self.add_error(
                "default_license",
                "If license is unset you must select a default license.",
            )

        if not section and not default_section:
            self.add_error(
                "default_section",
                "If section is unset you must select a default section.",
            )

        if not language and not default_language:
            self.add_error(
                "default_language",
                "If language is unset you must select a default language.",
            )

    class Meta:
        model = models.SubmissionConfiguration
        exclude = ("journal",)


class ProjectedIssueForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProjectedIssueForm, self).__init__(*args, **kwargs)
        self.fields["projected_issue"].queryset = self.instance.journal.issue_set.all()

    class Meta:
        model = models.Article
        fields = ("projected_issue",)


class ArticleFundingForm(forms.ModelForm):
    class Meta:
        model = models.ArticleFunding
        fields = ("name", "fundref_id", "funding_id", "funding_statement")
        widgets = {
            "funding_statement": TinyMCE(),
        }

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop("article", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True, *args, **kwargs):
        funder = super().save(commit=commit, *args, **kwargs)
        if self.article:
            funder.article = self.article
        if commit:
            funder.save()
        return funder


def utility_clean_orcid(orcid):
    warnings.warn("Use utils.forms.clean_orcid_id")
    return clean_orcid_id(orcid)


class PubDateForm(forms.ModelForm):
    class Meta:
        model = models.Article
        fields = ("date_published",)

    def save(self, commit=True):
        article = super().save(commit=commit)
        if commit:
            article.fixedpubcheckitems.set_pub_date = bool(article.date_published)
            article.fixedpubcheckitems.save()
            article.save()
        return article


class CreditRecordForm(forms.ModelForm):
    def _remove_choices_when_roles_already_exist(self, credit_records):
        credit_slugs = set(record.role for record in credit_records)
        new_choices = []
        for old_choice in self.fields["role"].choices:
            if old_choice[0] not in credit_slugs:
                new_choices.append(old_choice)
        self.fields["role"].choices = new_choices

    def __init__(self, *args, **kwargs):
        self.frozen_author = kwargs.pop("frozen_author", None)
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = self.fields["role"].choices[1:]

        if self.frozen_author:
            self._remove_choices_when_roles_already_exist(
                models.CreditRecord.objects.filter(
                    frozen_author=self.frozen_author,
                )
            )

    class Meta:
        model = models.CreditRecord
        fields = ("role",)
        widgets = {
            "role": forms.widgets.RadioSelect,
        }


class AuthorAffiliationForm(forms.ModelForm):
    """
    A form for author affiliations.
    Can be used by submitting authors during submission,
    or editors during the subsequent workflow.
    """

    class Meta:
        model = core_models.ControlledAffiliation
        fields = ("title", "department", "is_primary", "start", "end")
        widgets = {
            "start": HTMLDateInput,
            "end": HTMLDateInput,
            "is_primary": YesNoRadio,
        }

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop("journal", None)
        self.frozen_author = kwargs.pop("frozen_author", None)
        self.organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)
        if self.journal:
            if not self.journal.get_setting("general", "author_job_title"):
                self.fields.pop("title")
            if not self.journal.get_setting("general", "author_department"):
                self.fields.pop("department")
            if not self.journal.get_setting("general", "author_affiliation_dates"):
                self.fields.pop("start")
                self.fields.pop("end")

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance:
            # Todo: Does this ever run? Q is undefined.
            query = Q(account=self.frozen_author, organization=self.organization)
            for key, value in cleaned_data.items():
                query &= Q((key, value))
            if self._meta.model.objects.filter(query).exists():
                self.add_error(
                    None, "An affiliation with matching details already exists."
                )
        return cleaned_data

    def save(self, commit=True):
        affiliation = super().save(commit=False)
        affiliation.frozen_author = self.frozen_author
        affiliation.organization = self.organization
        if commit:
            affiliation.save()
        return affiliation

from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.text import slugify
from django.urls import resolve, Resolver404
from tinymce.widgets import TinyMCE


from submission import models as submission_models
from repository import models
from repository.logic import set_update_field_answers
from press import models as press_models
from review.logic import render_choices
from core import models as core_models, workflow
from utils import forms as utils_forms
from identifiers.models import URL_DOI_RE
from core.widgets import TableMultiSelectUser
from utils.logger import get_logger

logger = get_logger(__name__)


class PreSubmissionStartForm(forms.Form):
    submission_type = forms.ModelChoiceField(
        queryset=models.RepositorySubmissionType.objects.none(),
        required=True,
        label="Select the appropriate submission type. This will affect the metadata "
        "fields shown and the processing steps your submission follows.",
        widget=forms.RadioSelect,
    )

    submission_agreement = forms.BooleanField(
        required=True,
        label="I agree to the terms of submission",
    )

    organisation_unit = forms.ModelChoiceField(
        queryset=models.RepositoryOrganisationUnit.objects.none(),
        required=False,
        label="Organisational Unit",
        help_text="Select the relevant unit, department, or group for this submission.",
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        repository = kwargs.pop("repository")
        super().__init__(*args, **kwargs)

        self.fields[
            "submission_type"
        ].queryset = models.RepositorySubmissionType.objects.filter(
            repository=repository,
        )

        self.ou_depth_map = {}
        if not repository.has_organisation_units:
            del self.fields["organisation_unit"]
            return

        def walk(unit, level=0):
            self.ou_depth_map[str(unit.id)] = level
            yield (unit.id, unit.name)
            for child in unit.children.all().order_by("name"):
                yield from walk(child, level + 1)

        top_units = (
            models.RepositoryOrganisationUnit.objects.filter(
                repository=repository,
                parent__isnull=True,
            )
            .order_by("name")
            .prefetch_related("children")
        )

        choices = []
        for unit in top_units:
            choices.extend(walk(unit))

        self.fields["organisation_unit"].choices = choices
        self.fields[
            "organisation_unit"
        ].queryset = models.RepositoryOrganisationUnit.objects.filter(
            repository=repository,
        )


def build_additional_field(element):
    """
    Returns a form field for a repository custom field.
    :param element: RepositoryField
    """
    if element.input_type == "text":
        field = forms.CharField(
            widget=forms.TextInput(),
            required=element.required,
        )
    elif element.input_type == "textarea":
        field = forms.CharField(
            widget=forms.Textarea,
            required=element.required,
        )
    elif element.input_type == "date":
        field = forms.CharField(
            widget=forms.DateInput(attrs={"class": "datepicker"}),
            required=element.required,
        )
    elif element.input_type == "select":
        field = forms.ChoiceField(
            widget=forms.Select(),
            choices=render_choices(element.choices),
            required=element.required,
        )
    elif element.input_type == "email":
        field = forms.EmailField(
            widget=forms.TextInput(),
            required=element.required,
        )
    elif element.input_type == "checkbox":
        field = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={"is_checkbox": True}),
            required=element.required,
        )
    elif element.input_type == "number":
        field = forms.IntegerField(
            required=element.required,
        )
    else:
        field = forms.CharField(
            widget=forms.Textarea(),
            required=element.required,
        )

    if element.input_type == "date":
        field.help_text = f"Use ISO 8601 Date Format YYYY-MM-DD. {element.help_text}"
    else:
        field.help_text = element.help_text
    field.label = element.name
    return field


def additional_field_answer_text(element, value):
    """
    Converts a cleaned custom field value to the text stored on
    RepositoryFieldAnswer, matching what the submission form stores:
    checkboxes are "on" when ticked, and empty values are not stored.
    :return: str, or None if there is no answer to store
    """
    if element.input_type == "checkbox":
        return "on" if value else None
    if value in (None, ""):
        return None
    return str(value)


class PreprintInfo(utils_forms.KeywordModelForm):
    subject = forms.ModelMultipleChoiceField(
        required=True,
        queryset=models.Subject.objects.none(),
        widget=forms.SelectMultiple(attrs={"multiple": ""}),
    )

    class Meta:
        model = models.Preprint
        fields = (
            "title",
            "abstract",
            "license",
            "comments_editor",
            "subject",
            "doi",
            "peer_reviewed",
        )
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": _("Title")}),
            "abstract": forms.Textarea(
                attrs={"placeholder": _("Enter your article's abstract here")}
            ),
            "peer_reviewed": forms.NullBooleanSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.admin = kwargs.pop("admin", False)
        self.submission_type_slug = kwargs.pop("submission_type_slug", None)
        super(PreprintInfo, self).__init__(*args, **kwargs)

        if (
            not self.submission_type_slug
            and self.instance
            and self.instance.submission_type
        ):
            self.submission_type_slug = self.instance.submission_type.slug

        elements = self.request.repository.type_additional_submission_fields(
            submission_type_slug=self.submission_type_slug,
        )
        if self.admin:
            self.fields.pop("comments_editor")

        self.fields["subject"].queryset = models.Subject.objects.filter(
            enabled=True,
            repository=self.request.repository,
        )

        if self.admin:
            self.fields["license"].queryset = submission_models.Licence.objects.filter(
                journal__isnull=True,
            )
        else:
            self.fields[
                "license"
            ].queryset = self.request.repository.active_licenses.all()

        # Requiring a licence when the repository has configured none leaves
        # the author with a mandatory field they cannot satisfy, which blocks
        # submission entirely.
        licences_available = self.fields["license"].queryset.exists()
        self.fields["license"].required = licences_available
        if not licences_available:
            self.fields["license"].help_text = _(
                "No licences have been configured for this repository. "
                "Please contact the repository team."
            )
            logger.warning(
                "Repository %s has no active licences, so the submission "
                "licence field cannot be completed.",
                self.request.repository,
            )

        if elements:
            for element in elements:
                self.fields[element.name] = build_additional_field(element)

                preprint = kwargs["instance"]
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
        doi_string = self.cleaned_data.get("doi")

        if doi_string and not URL_DOI_RE.match(doi_string):
            self.add_error(
                "doi",
                "DOIs should be in the following format: https://doi.org/10.XXX/XXXXX",
            )

        return doi_string


class PreprintSupplementaryFileForm(forms.ModelForm):
    """
    Adds a supplementary file: a link, or, on institutional repositories, an
    uploaded file with its document version. Moderators can also set an
    uploaded file's access.
    """

    upload = forms.FileField(
        required=False,
        label=_("Or upload a file"),
    )
    document_version = forms.ChoiceField(
        required=False,
        label=_("Document version"),
        choices=(("", "---------"),) + models.PreprintFile.DOCUMENT_VERSION_CHOICES,
    )
    access = forms.ChoiceField(
        required=False,
        label=_("Access"),
        choices=models.PreprintFile.ACCESS_CHOICES,
        initial=models.PreprintFile.ACCESS_OPEN,
    )
    embargo_until = forms.DateField(
        required=False,
        label=_("Embargo end"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = models.PreprintSupplementaryFile
        fields = (
            "label",
            "url",
        )

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop("preprint")
        # Adding to a draft update's list rather than the preprint's. A
        # moderator checks the update, so its author can set access.
        self.version_queue = kwargs.pop("version_queue", None)
        self.can_set_access = kwargs.pop("can_set_access", False) or bool(
            self.version_queue
        )
        super(PreprintSupplementaryFileForm, self).__init__(*args, **kwargs)
        self.allow_upload = self.preprint.repository.is_institutional
        # Blank labels are filled in from the file name or the link, so the
        # record never lists entries called "Additional file".
        self.fields["label"].required = False
        self.fields["label"].initial = ""
        self.fields["label"].help_text = _(
            "How it's listed on the record. The file name or link if left blank."
        )
        if self.allow_upload:
            self.fields["url"].required = False
            self.fields["url"].label = _("Link")
        else:
            # Links only, as before uploads existed.
            self.fields["url"].required = True
            for name in ("upload", "document_version", "access", "embargo_until"):
                del self.fields[name]
        if not (self.allow_upload and self.can_set_access):
            self.fields.pop("access", None)
            self.fields.pop("embargo_until", None)

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get("url")
        upload = cleaned_data.get("upload")
        if self.allow_upload:
            if url and upload:
                raise forms.ValidationError(
                    _("Give a link or upload a file, not both.")
                )
            if not url and not upload:
                raise forms.ValidationError(_("Give a link or upload a file."))
        if not cleaned_data.get("label"):
            cleaned_data["label"] = (upload.name if upload else (url or ""))[:200]
        access = cleaned_data.get("access")
        if access == models.PreprintFile.ACCESS_EMBARGOED and not cleaned_data.get(
            "embargo_until"
        ):
            self.add_error("embargo_until", _("Give the date the embargo ends."))
        return cleaned_data

    def save(self, commit=True):
        link = super(PreprintSupplementaryFileForm, self).save(commit=False)
        if self.version_queue is not None:
            link.preprint = None
            link.version_queue = self.version_queue
            last = self.version_queue.supplementary_entries.order_by("-order").first()
            link.order = (last.order + 1) if last else 0
        else:
            link.preprint = self.preprint
        upload = self.cleaned_data.get("upload")
        if upload:
            access = self.cleaned_data.get("access") or models.PreprintFile.ACCESS_OPEN
            preprint_file = models.PreprintFile(
                preprint=self.preprint,
                file=upload,
                original_filename=upload.name,
                document_version=self.cleaned_data.get("document_version") or "",
                access=access,
                embargo_until=(
                    self.cleaned_data.get("embargo_until")
                    if access == models.PreprintFile.ACCESS_EMBARGOED
                    else None
                ),
            )
            preprint_file.save()
            preprint_file.mime_type = preprint_file.get_file_mime_type()
            preprint_file.size = preprint_file.file.size
            preprint_file.save(update_fields=["mime_type", "size"])
            link.file = preprint_file
            link.url = ""
            if self.version_queue is None:
                link.order = self.preprint.next_supp_file_order()
        if commit:
            link.save()

        return link


class CommentForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ("body",)

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop("preprint", None)
        self.author = kwargs.pop("author", None)
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
            "preprints_about",
            "preprint_start",
            "preprint_submission",
            "preprint_publication",
            "preprint_decline",
            "preprint_pdf_only",
        )
        widgets = {
            "preprints_about": TinyMCE,
            "preprint_start": TinyMCE,
            "preprint_submission": TinyMCE,
            "preprint_publication": TinyMCE,
            "preprint_decline": TinyMCE,
        }

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            press = kwargs["instance"]
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
                setting.value = "On" if self.cleaned_data[setting.name] else ""
            else:
                setting.value = self.cleaned_data[setting.name]
            setting.save()


class SubjectForm(forms.ModelForm):
    class Meta:
        model = models.Subject
        exclude = ("repository", "slug")

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository")
        super(SubjectForm, self).__init__(*args, **kwargs)
        self.fields["parent"].queryset = models.Subject.objects.filter(
            repository=self.repository,
        )

    def save(self, commit=True):
        subject = super(SubjectForm, self).save(commit=False)
        subject.repository = self.repository
        subject.slug = slugify(subject.name)

        if commit:
            subject.save()

        return subject


class OrganisationUnitForm(forms.ModelForm):
    class Meta:
        model = models.RepositoryOrganisationUnit
        fields = ("name", "code", "parent")

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository")
        super(OrganisationUnitForm, self).__init__(*args, **kwargs)
        parents = models.RepositoryOrganisationUnit.objects.filter(
            repository=self.repository,
        )
        if self.instance.pk:
            # A unit cannot be moved underneath itself or one of its children.
            excluded = [self.instance.pk] + [
                unit.pk for unit in self.instance.get_descendants()
            ]
            parents = parents.exclude(pk__in=excluded)
        self.fields["parent"].queryset = parents

    def clean_code(self):
        code = self.cleaned_data["code"]
        clashes = models.RepositoryOrganisationUnit.objects.filter(
            repository=self.repository,
            code=code,
        ).exclude(pk=self.instance.pk)
        if clashes.exists():
            raise forms.ValidationError(
                _("Another unit in this repository already uses this code."),
            )

        # Unit home pages live at /repository/<code>/, after the other
        # repository URLs, so a code like "about" would never be reachable.
        # Resolve against the repository URLs directly so the site's path
        # prefix (in path mode) doesn't affect the check.
        try:
            match = resolve(f"/{code}/", urlconf="repository.urls")
        except Resolver404:
            match = None
        if not match or match.url_name != "repository_home_by_rou":
            raise forms.ValidationError(
                _("This code is reserved by another page. Choose a different code."),
            )
        return code

    def save(self, commit=True):
        unit = super(OrganisationUnitForm, self).save(commit=False)
        unit.repository = self.repository

        if commit:
            unit.save()

        return unit


class OrganisationUnitSettingsForm(forms.ModelForm):
    class Meta:
        model = models.Repository
        fields = (
            "enable_organisation_units",
            "rou_default_name",
            "rou_struct_page_text",
        )
        labels = {
            "enable_organisation_units": _("Enable organisational units"),
            "rou_default_name": _("Name for organisational units"),
            "rou_struct_page_text": _("Organisational structure page text"),
        }
        help_texts = {
            "enable_organisation_units": _(
                "Show units on the public site and in the submission form. "
                "Turning this off hides them without deleting any units or "
                "their links to submissions."
            ),
        }
        widgets = {
            "rou_struct_page_text": TinyMCE,
        }


class ActiveLicenseForm(forms.ModelForm):
    class Meta:
        model = models.Repository
        fields = ("active_licenses",)
        widgets = {
            "active_licenses": forms.CheckboxSelectMultiple,
        }
        labels = {
            "active_licenses": "Select the licenses that authors can pick from during submission",
        }

    def __init__(self, *args, **kwargs):
        super(ActiveLicenseForm, self).__init__(*args, **kwargs)
        self.fields[
            "active_licenses"
        ].queryset = submission_models.Licence.objects.filter(journal=None)
        self.fields["active_licenses"].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        return obj.name


class FileForm(forms.ModelForm):
    class Meta:
        model = models.PreprintFile
        fields = ("file",)

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop("preprint")
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
        fields = ("title", "abstract", "published_doi")
        widgets = {
            "title": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop("preprint")
        super(VersionForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["title"].initial = self.preprint.title
            self.fields["abstract"].initial = self.preprint.abstract
            self.fields["published_doi"].initial = self.preprint.doi

    def save(self, commit=True):
        version = super(VersionForm, self).save(commit=False)
        version.preprint = self.preprint

        if commit:
            version.save()

        return version

    def clean_published_doi(self):
        doi_string = self.cleaned_data.get("published_doi")

        if doi_string and not URL_DOI_RE.match(doi_string):
            self.add_error(
                "published_doi",
                "DOIs should be in the following format: https://doi.org/10.XXX/XXXXX",
            )

        return doi_string


class UpdateFieldAnswersForm(forms.Form):
    """
    A draft update's answers to the repository's custom fields.
    """

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop("preprint")
        self.version_queue = kwargs.pop("version_queue")
        super().__init__(*args, **kwargs)
        self.elements = list(
            self.preprint.repository.type_additional_submission_fields(
                submission_type_slug=(
                    self.preprint.submission_type.slug
                    if self.preprint.submission_type
                    else None
                ),
            )
        )
        answers = {
            answer.field_id: answer.answer
            for answer in self.version_queue.repositoryfieldanswer_set.all()
        }
        for element in self.elements:
            field = build_additional_field(element)
            answer = answers.get(element.pk)
            if isinstance(field, forms.ChoiceField):
                # Without these, the browser would post the first choice for
                # a field with no answer, or for an answer that is no longer
                # a choice.
                choices = list(field.choices)
                if answer and answer not in dict(choices):
                    choices.insert(0, (answer, answer))
                if not element.required or not answer:
                    choices.insert(0, ("", "---------"))
                field.choices = choices
            field.initial = bool(answer) if element.input_type == "checkbox" else answer
            self.fields[self.field_name(element)] = field

    @staticmethod
    def field_name(element):
        return f"field_{element.pk}"

    def save(self):
        set_update_field_answers(
            self.version_queue,
            {
                element: additional_field_answer_text(
                    element,
                    self.cleaned_data.get(self.field_name(element)),
                )
                for element in self.elements
            },
        )


class RepositoryBase(forms.ModelForm):
    # Settings for institutional repository features, hidden on preprint
    # servers.
    INSTITUTIONAL_FIELDS = (
        "request_copy",
        "copy_request_to_author",
        "copy_request_approved",
        "copy_request_declined",
        "copy_request_expired",
    )

    class Meta:
        model = models.Repository
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.press = kwargs.pop("press")
        super(RepositoryBase, self).__init__(*args, **kwargs)
        if not (self.instance and self.instance.pk and self.instance.is_institutional):
            for name in self.INSTITUTIONAL_FIELDS:
                self.fields.pop(name, None)


class RepositoryInitial(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = (
            "name",
            "short_name",
            "domain",
            "object_name",
            "object_name_plural",
            "repository_type",
            "theme",
            "display_public_metrics",
            "publisher",
        )
        help_texts = {
            "domain": "Using a custom domain requires configuring DNS. "
            "The repository will always be available under the /code path",
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
            "headless_mode",
            "identifier_management",
            "about",
            "logo",
            "hero_background",
            "favicon",
            "footer",
            "login_text",
            "limit_access_to_submission",
            "submission_access_request_text",
            "submission_access_contact",
            "review_submission_text",
            "custom_js_code",
            "review_helper",
        )
        widgets = {
            "about": TinyMCE,
            "footer": TinyMCE,
            "login_text": TinyMCE,
            "submission_access_request_text": TinyMCE,
            "review_helper": TinyMCE,
        }


class RepositorySubmission(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = (
            "start",
            "file_upload_help",
            "submission_agreement",
            "submission_file_required",
            "host_ror_id",
            "request_copy",
            "limit_upload_to_pdf",
            "require_pdf_help",
            "additional_version_help",
            "managers",
            "moderators",
        )

        widgets = {
            "start": TinyMCE,
            "submission_agreement": TinyMCE,
            "file_upload_help": TinyMCE,
            "additional_version_help": TinyMCE,
            "managers": FilteredSelectMultiple(
                "Accounts",
                False,
                attrs={"rows": "2"},
            ),
            "moderators": FilteredSelectMultiple(
                "Accounts",
                False,
                attrs={"rows": "2"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow a pasted https://ror.org/ link; clean_host_ror_id trims it.
        field = self.fields["host_ror_id"]
        field.max_length = None
        field.validators = [
            validator
            for validator in field.validators
            if not isinstance(validator, MaxLengthValidator)
        ]
        field.widget.attrs.pop("maxlength", None)

    def clean_host_ror_id(self):
        """Takes a bare ROR ID or its https://ror.org/ link."""
        ror_id = self.cleaned_data.get("host_ror_id", "").strip().rstrip("/")
        for prefix in ("https://ror.org/", "http://ror.org/", "ror.org/"):
            if ror_id.lower().startswith(prefix):
                ror_id = ror_id[len(prefix) :]
        if (
            ror_id
            and not core_models.Organization.objects.filter(ror_id=ror_id).exists()
        ):
            raise forms.ValidationError(
                _(
                    "No organisation with the ROR ID %(ror_id)s has been "
                    "imported into Janeway yet."
                ),
                params={"ror_id": ror_id},
            )
        return ror_id


class RepositoryEmails(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = (
            "submission_notification_recipients",
            "submission",
            "publication",
            "decline",
            "accept_version",
            "decline_version",
            "new_comment",
            "comment_published",
            "comment_approved",
            "review_invitation",
            "manager_review_status_change",
            "reviewer_review_status_change",
            "new_version_submitted",
            "copy_request_to_author",
            "copy_request_approved",
            "copy_request_declined",
            "copy_request_expired",
        )

        widgets = {
            "submission": TinyMCE,
            "publication": TinyMCE,
            "copy_request_to_author": TinyMCE,
            "copy_request_approved": TinyMCE,
            "copy_request_declined": TinyMCE,
            "copy_request_expired": TinyMCE,
            "decline": TinyMCE,
            "accept_version": TinyMCE,
            "decline_version": TinyMCE,
            "new_comment": TinyMCE,
            "comment_published": TinyMCE,
            "comment_approved": TinyMCE,
            "review_invitation": TinyMCE,
            "manager_review_status_change": TinyMCE,
            "reviewer_review_status_change": TinyMCE,
            "new_version_submitted": TinyMCE,
            "submission_notification_recipients": TableMultiSelectUser(),
        }

    def __init__(self, *args, **kwargs):
        super(RepositoryEmails, self).__init__(*args, **kwargs)
        repo_managers = kwargs["instance"].moderating_accounts()
        self.fields["submission_notification_recipients"].queryset = repo_managers
        self.fields["submission_notification_recipients"].choices = [
            (m.id, {"name": m.full_name(), "email": m.email}) for m in repo_managers
        ]


class RepositoryLiveForm(RepositoryBase):
    class Meta:
        model = models.Repository
        fields = ("live",)


class RepositoryFieldForm(forms.ModelForm):
    class Meta:
        model = models.RepositoryField
        fields = (
            "name",
            "submission_type",
            "input_type",
            "choices",
            "required",
            "order",
            "help_text",
            "display",
            "dc_metadata_type",
        )

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository")
        super(RepositoryFieldForm, self).__init__(*args, **kwargs)
        self.fields[
            "submission_type"
        ].queryset = models.RepositorySubmissionType.objects.filter(
            repository=self.repository,
        )

    def save(self, commit=True):
        field = super(RepositoryFieldForm, self).save(commit=False)
        field.repository = self.repository

        if commit:
            field.save()

        return field


class PreprinttoArticleForm(forms.Form):
    license = forms.ModelChoiceField(queryset=submission_models.Licence.objects.none())
    section = forms.ModelChoiceField(queryset=submission_models.Section.objects.none())
    stage = forms.ChoiceField(choices=())
    force = forms.BooleanField(
        required=False,
        help_text="If you want to force the creation of a new article object even if one exists, check this box. "
        "The old article will be orphaned and no longer linked to this object.",
    )

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop("journal", None)
        super(PreprinttoArticleForm, self).__init__(*args, **kwargs)

        if self.journal:
            self.fields["license"].queryset = submission_models.Licence.objects.filter(
                journal=self.journal,
            )
            self.fields["section"].queryset = submission_models.Section.objects.filter(
                journal=self.journal,
            )
            self.fields["stage"].choices = workflow.workflow_journal_choices(
                self.journal
            )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = models.Review
        fields = (
            "reviewer",
            "date_due",
        )
        widgets = {
            "date_due": utils_forms.HTMLDateInput(),
        }

    def __init__(self, *args, **kwargs):
        self.preprint = kwargs.pop("preprint")
        self.manager = kwargs.pop("manager")
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.fields["reviewer"].queryset = self.preprint.repository.reviewer_accounts()

    def save(self, commit=True):
        review = super(ReviewForm, self).save(commit=False)
        review.preprint = self.preprint
        review.manager = self.manager
        review.status = "new"

        if commit:
            review.save()

        return review


class ReviewDueDateForm(forms.ModelForm):
    class Meta:
        model = models.Review
        fields = ("date_due",)
        widgets = {
            "date_due": utils_forms.HTMLDateInput(),
        }


class ReviewCommentForm(forms.Form):
    body = forms.CharField(
        widget=TinyMCE(),
        label="Comments",
    )
    recommendation = forms.ModelChoiceField(
        queryset=models.ReviewRecommendation.objects.none(),
    )
    anonymous = forms.BooleanField(
        help_text="Check if you want your comments to be displayed anonymously.",
        label="Comment Anonymously",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.review = kwargs.pop("review")
        super(ReviewCommentForm, self).__init__(*args, **kwargs)
        if self.review.comment:
            self.fields["body"].initial = self.review.comment.body
            self.fields["anonymous"].initial = self.review.anonymous
            self.fields["recommendation"].initial = self.review.recommendation.pk

        self.fields[
            "recommendation"
        ].queryset = models.ReviewRecommendation.objects.filter(
            repository=self.review.preprint.repository,
            active=True,
        )

    def save(self):
        if self.cleaned_data:
            if self.review.comment:
                comment = self.review.comment
            else:
                comment = models.Comment()

            comment.author = self.review.reviewer
            comment.preprint = self.review.preprint
            comment.body = self.cleaned_data.get("body")
            comment.save()

            self.review.anonymous = self.cleaned_data.get("anonymous", False)
            self.review.comment = comment
            self.review.recommendation = self.cleaned_data.get("recommendation")
            self.review.save()


class RecommendationForm(forms.ModelForm):
    class Meta:
        model = models.ReviewRecommendation
        fields = (
            "name",
            "active",
        )

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository")
        super(RecommendationForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        recommendation = super(RecommendationForm, self).save(commit=False)
        recommendation.repository = self.repository

        if commit:
            recommendation.save()

        return recommendation


class PreprintFilterForm(forms.Form):
    SEARCH_FIELDS = (
        "title",
        "abstract",
        "authors",
        "keywords",
        "full_text",
        "orcid",
    )
    DEFAULT_SEARCH_FIELDS = ("title", "abstract", "authors")
    SORT_CHOICES = (
        ("", _("Default")),
        ("-date_published", _("Newest first")),
        ("date_published", _("Oldest first")),
        ("title", _("Title (A-Z)")),
        ("-title", _("Title (Z-A)")),
    )

    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Search..."}),
    )
    # No CSS classes on these widgets. Three themes render this form and each
    # has its own form library, so a class from one is meaningless in the
    # others. The templates apply their own styling.
    sort = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        label="Sort by",
    )
    subject = forms.ModelChoiceField(
        queryset=models.Subject.objects.none(),
        required=False,
        label="Subject",
        empty_label="— All Subjects —",
    )

    submission_type = forms.ModelChoiceField(
        queryset=models.RepositorySubmissionType.objects.none(),
        required=False,
        label="Submission Type",
        empty_label="— All Types —",
    )

    title = forms.BooleanField(required=False, initial=True)
    abstract = forms.BooleanField(required=False, initial=True)
    authors = forms.BooleanField(required=False, initial=True)
    keywords = forms.BooleanField(required=False)
    full_text = forms.BooleanField(required=False)
    orcid = forms.BooleanField(required=False, label="ORCID")

    def __init__(self, *args, repository=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound:
            self.apply_default_search_fields()
        if repository:
            self.fields["subject"].queryset = models.Subject.objects.filter(
                repository=repository,
                enabled=True,
            )
            self.fields[
                "submission_type"
            ].queryset = models.RepositorySubmissionType.objects.filter(
                repository=repository,
            )

    def apply_default_search_fields(self):
        """Restores the default search fields when a term was given without any.

        ``initial`` only applies to unbound forms, so a search submitted from a
        plain search box arrives with every field flag absent, which cleans to
        False. That would search no fields at all and match nothing.

        Applied to the submitted data rather than in clean() so that the
        checkboxes render ticked and the reader can see what was searched.
        """
        if not self.data.get("search_term"):
            return
        if any(self.data.get(field) for field in self.SEARCH_FIELDS):
            return
        data = self.data.copy()
        for field in self.DEFAULT_SEARCH_FIELDS:
            data[field] = "on"
        self.data = data

    def search_filters(self):
        if not self.is_valid():
            return {}
        return {
            "title": self.cleaned_data.get("title", False),
            "abstract": self.cleaned_data.get("abstract", False),
            "authors": self.cleaned_data.get("authors", False),
            "keywords": self.cleaned_data.get("keywords", False),
            "full_text": self.cleaned_data.get("full_text", False),
            "ORCID": self.cleaned_data.get("orcid", False),
        }


class RepositorySubmissionTypeForm(forms.ModelForm):
    class Meta:
        model = models.RepositorySubmissionType
        fields = [
            "name",
            "name_plural",
            "slug",
            "default_peer_reviewed",
            "pill_colour",
        ]
        help_texts = {
            "slug": (
                "A URL-safe identifier for this type (e.g. 'preprint'). "
                "Used in HTML classes and API filters. Must be unique within this site."
            ),
            "pill_colour": ("Hex colour code used to style the label (e.g. #1e40af)."),
        }
        widgets = {
            "pill_colour": forms.TextInput(attrs={"placeholder": "#1e40af"}),
        }


class PreprintFileAccessForm(forms.ModelForm):
    class Meta:
        model = models.PreprintFile
        fields = ("access", "embargo_until", "document_version")
        widgets = {"embargo_until": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned_data = super().clean()
        access = cleaned_data.get("access")
        if access == models.PreprintFile.ACCESS_EMBARGOED:
            if not cleaned_data.get("embargo_until"):
                self.add_error(
                    "embargo_until",
                    _("Give the date the embargo ends."),
                )
        else:
            # Only an embargo has an end date.
            cleaned_data["embargo_until"] = None
        return cleaned_data


class CopyRequestForm(utils_forms.CaptchaForm, forms.ModelForm):
    class Meta:
        model = models.CopyRequest
        fields = ("name", "email", "reason")
        widgets = {"reason": forms.Textarea(attrs={"rows": 4})}


class CopyRequestAuthorForm(forms.ModelForm):
    """Which of the record's authors is asked when readers request a copy."""

    class Meta:
        model = models.Preprint
        fields = ("copy_request_author",)
        labels = {"copy_request_author": _("Author asked for copies")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["copy_request_author"]
        field.queryset = self.instance.frozen_authors()
        field.label_from_instance = lambda author: "{}{}".format(
            author.full_name(),
            " ({})".format(author.email) if author.email else " (no email)",
        )
        field.empty_label = _("The owner")

    def clean_copy_request_author(self):
        author = self.cleaned_data.get("copy_request_author")
        if author is not None and not author.email:
            raise forms.ValidationError(_("This author has no email address."))
        return author


ACCESS_HELP = _(
    "Embargoed files open to everyone on the end date; restricted files "
    "stay with the repository team."
)


class AccessFieldsMixin:
    """Access, embargo end and document version for an uploaded file."""

    def add_access_fields(
        self, initial_access="", initial_until=None, initial_version=""
    ):
        self.fields["document_version"] = forms.ChoiceField(
            required=False,
            label=_("What is this file?"),
            choices=(("", _("Not given")),)
            + models.PreprintFile.DOCUMENT_VERSION_CHOICES,
            initial=initial_version,
        )
        self.fields["access"] = forms.ChoiceField(
            label=_("Who can download it"),
            choices=models.PreprintFile.ACCESS_CHOICES,
            initial=initial_access or models.PreprintFile.ACCESS_OPEN,
            help_text=ACCESS_HELP,
            widget=forms.Select(attrs={"data-access-select": ""}),
        )
        self.fields["embargo_until"] = forms.DateField(
            required=False,
            label=_("Embargo end"),
            initial=initial_until,
            widget=forms.DateInput(attrs={"type": "date", "data-embargo-date": ""}),
        )

    def clean_access_fields(self, cleaned_data):
        if cleaned_data.get("access") == models.PreprintFile.ACCESS_EMBARGOED:
            if not cleaned_data.get("embargo_until"):
                self.add_error("embargo_until", _("Give the date the embargo ends."))
        else:
            cleaned_data["embargo_until"] = None
        return cleaned_data


def save_uploaded_file(preprint, upload, cleaned_data):
    preprint_file = models.PreprintFile(
        preprint=preprint,
        file=upload,
        original_filename=upload.name,
        document_version=cleaned_data.get("document_version") or "",
        access=cleaned_data.get("access") or models.PreprintFile.ACCESS_OPEN,
        embargo_until=cleaned_data.get("embargo_until"),
    )
    preprint_file.save()
    preprint_file.mime_type = preprint_file.get_file_mime_type()
    preprint_file.size = preprint_file.file.size
    preprint_file.save(update_fields=["mime_type", "size"])
    return preprint_file


def next_draft_order(update):
    last = update.supplementary_entries.order_by("-order").first()
    return (last.order + 1) if last else 0


class AdditionalUploadForm(AccessFieldsMixin, forms.Form):
    """Upload a file to a draft update's additional files."""

    upload = forms.FileField(label=_("File"))
    label = forms.CharField(
        required=False,
        max_length=200,
        label=_("Label"),
        help_text=_("How it's listed on the record. The file name if left blank."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_access_fields()

    def clean(self):
        return self.clean_access_fields(super().clean())

    def save(self, preprint, update):
        upload = self.cleaned_data["upload"]
        preprint_file = save_uploaded_file(preprint, upload, self.cleaned_data)
        return models.PreprintSupplementaryFile.objects.create(
            version_queue=update,
            file=preprint_file,
            label=self.cleaned_data.get("label") or upload.name,
            order=next_draft_order(update),
        )


class AdditionalLinkForm(forms.Form):
    """Add a link to a draft update's additional files."""

    url = forms.URLField(label=_("Link"))
    label = forms.CharField(
        required=False,
        max_length=200,
        label=_("Label"),
        help_text=_("How it's listed on the record. The link if left blank."),
    )

    def save(self, preprint, update):
        url = self.cleaned_data["url"]
        return models.PreprintSupplementaryFile.objects.create(
            version_queue=update,
            url=url,
            label=self.cleaned_data.get("label") or url[:200],
            order=next_draft_order(update),
        )


class AdditionalEditForm(AccessFieldsMixin, forms.Form):
    """Change an entry on a draft update's list: its label, and for an
    upload, what it is, who can download it, or the file itself."""

    label = forms.CharField(max_length=200, label=_("Label"))

    def __init__(self, *args, entry=None, **kwargs):
        self.entry = entry
        super().__init__(*args, **kwargs)
        self.fields["label"].initial = entry.label
        if entry.is_upload:
            self.fields["replace"] = forms.FileField(
                required=False, label=_("Replace the file")
            )
            self.add_access_fields(
                entry.effective_access,
                entry.effective_embargo_until,
                entry.effective_document_version,
            )
        else:
            self.fields["url"] = forms.URLField(label=_("Link"), initial=entry.url)

    def clean(self):
        cleaned_data = super().clean()
        if self.entry.is_upload:
            cleaned_data = self.clean_access_fields(cleaned_data)
        return cleaned_data

    def save(self, preprint, update):
        from repository import logic

        entry = self.entry
        entry.label = self.cleaned_data["label"]
        if not entry.is_upload:
            entry.url = self.cleaned_data["url"]
            entry.save()
            return entry
        replace = self.cleaned_data.get("replace")
        access = self.cleaned_data.get("access")
        until = self.cleaned_data.get("embargo_until")
        version = self.cleaned_data.get("document_version") or ""
        if replace:
            old = entry.file
            entry.file = save_uploaded_file(preprint, replace, self.cleaned_data)
            entry.proposed_access = ""
            entry.proposed_embargo_until = None
            entry.proposed_document_version = ""
            entry.save()
            logic.delete_unused_draft_file(old)
            return entry
        preprint_file = entry.file
        if not logic.file_used_outside_draft(update, preprint_file):
            # Only this draft uses the file: change it directly.
            preprint_file.access = access
            preprint_file.embargo_until = until
            preprint_file.document_version = version
            preprint_file.save(
                update_fields=["access", "embargo_until", "document_version"]
            )
        else:
            # Shared with the live record until approval: propose the change.
            same_access = (access, until) == (
                preprint_file.access,
                preprint_file.embargo_until,
            )
            entry.proposed_access = "" if same_access else access
            entry.proposed_embargo_until = None if same_access else until
            entry.proposed_document_version = (
                "" if version == preprint_file.document_version else version
            )
        entry.save()
        return entry


class PreprintFundingForm(forms.ModelForm):
    """A funder and grant on a record or an update's draft."""

    class Meta:
        model = submission_models.ArticleFunding
        fields = ("name", "funding_id", "fundref_id", "funding_statement")
        labels = {
            "name": _("Funder"),
            "funding_id": _("Grant number"),
            "fundref_id": _("Funder ID"),
            "funding_statement": _("Funding statement"),
        }
        help_texts = {
            "name": _("For example UK Research and Innovation."),
            "funding_id": _("Optional."),
            "fundref_id": _(
                "Optional: the funder's Crossref Funder ID or ROR ID, as a link, "
                "e.g. https://doi.org/10.13039/100014013."
            ),
            "funding_statement": _("Optional."),
        }
        widgets = {"funding_statement": forms.Textarea(attrs={"rows": 3})}


class PublicationDetailsForm(forms.ModelForm):
    """Where and when an institutional repository's record was published."""

    class Meta:
        model = models.PublicationDetails
        fields = models.PublicationDetails.DETAIL_FIELDS
        widgets = {
            name: forms.DateInput(attrs={"type": "date"})
            for name in (
                "accepted_date",
                "first_online_date",
                "publication_date",
                "completion_date",
                "submitted_date",
            )
        } | {
            "editors": forms.Textarea(attrs={"rows": 3}),
            "citation": forms.Textarea(attrs={"rows": 3}),
        }

    def save_for(self, **owner):
        """Save against an owner (preprint=…, version_queue=…), unless it's
        new and empty."""
        details = self.save(commit=False)
        for key, value in owner.items():
            setattr(details, key, value)
        if details.pk or not details.is_empty:
            details.save()
        return details

import logging
import uuid

from rest_framework import exceptions, serializers, validators

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import reverse
from django.utils import timezone

from core import models as core_models, logic as core_logic
from journal import models as journal_models
from submission import models as submission_models
from repository import models as repository_models
from identifiers import models as identifier_models
from events import logic as event_logic
from repository import forms as repository_forms, logic as repository_logic
from utils import orcid as orcid_utils
from utils.forms import plain_text_validator

logger = logging.getLogger(__name__)


class LicenceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = submission_models.Licence
        fields = ("pk", "name", "short_name", "text", "url")


class KeywordsSerializer(serializers.HyperlinkedModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        if "word" in fields:
            fields["word"].validators = [
                validator
                for validator in fields["word"].validators
                if not isinstance(validator, validators.UniqueValidator)
            ]
        return fields

    def create(self, validated_data):
        keyword, create = submission_models.Keyword.objects.get_or_create(
            word=validated_data.get("word"),
        )
        return keyword

    class Meta:
        model = submission_models.Keyword
        fields = ("word",)


class FrozenAuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = submission_models.FrozenAuthor
        fields = (
            "first_name",
            "middle_name",
            "last_name",
            "name_suffix",
            "institution",
            "department",
            "country",
        )

    country = serializers.ReadOnlyField(
        read_only=True,
        source="country.name",
    )


class GalleySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = core_models.Galley
        fields = ("label", "type", "path")


class ArticleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = submission_models.Article
        fields = (
            "pk",
            "title",
            "subtitle",
            "abstract",
            "language",
            "license",
            "keywords",
            "section",
            "is_remote",
            "remote_url",
            "frozenauthors",
            "date_submitted",
            "date_accepted",
            "date_published",
            "render_galley",
            "galleys",
        )

    license = LicenceSerializer()
    keywords = KeywordsSerializer(
        many=True,
        read_only=True,
    )
    section = serializers.ReadOnlyField(read_only=True, source="section.name")
    frozenauthors = FrozenAuthorSerializer(
        many=True,
        source="frozenauthor_set",
    )
    render_galley = GalleySerializer(
        read_only=True,
    )
    galleys = GalleySerializer(source="galley_set", many=True)


class PreprintSubjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = repository_models.Subject
        fields = ("name",)


class PreprintSubjectGroupSerializer(serializers.HyperlinkedModelSerializer):
    preprints = serializers.SerializerMethodField()

    class Meta:
        model = repository_models.Subject
        fields = ("name", "preprints")

    def get_preprints(self, obj):
        # You can filter or modify the queryset here
        custom_queryset = repository_models.Preprint.objects.filter(
            subject=obj,
            date_published__isnull=False,
            stage=repository_models.STAGE_PREPRINT_PUBLISHED,
        )
        request = self.context.get("request")
        format = self.context.get(
            "format",
            None,
        )
        view_name = "repository_preprints-detail"
        return [
            serializers.HyperlinkedIdentityField(view_name=view_name).get_url(
                preprint, "repository_preprints-detail", request, format
            )
            for preprint in custom_queryset
        ]


class PreprintFileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.PreprintFile
        fields = (
            "pk",
            "original_filename",
            "file",
            "preprint",
            "mime_type",
            "public_download_url",
            "manager_download_url",
        )

    manager_download_url = serializers.SerializerMethodField(
        method_name="get_manager_url",
    )
    public_download_url = serializers.SerializerMethodField(
        method_name="get_public_url",
    )

    def validate_preprint(self, preprint):
        """
        Files can only be added to preprints in this repository that the
        user owns, unless they are staff or a manager of the repository.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        repository = getattr(request, "repository", None)
        if repository is not None and preprint.repository != repository:
            raise serializers.ValidationError(
                "This preprint does not belong to this repository."
            )
        if not user or not (
            preprint.owner == user
            or user.is_staff
            or user.is_repository_manager(preprint.repository)
        ):
            raise serializers.ValidationError(
                "You can only add files to your own preprints."
            )
        return preprint

    def get_manager_url(self, obj):
        return obj.preprint.repository.site_url(
            path=reverse(
                "repository_download_file",
                kwargs={
                    "preprint_id": obj.preprint.pk,
                    "file_id": obj.pk,
                },
            )
        )

    def get_public_url(self, obj):
        return obj.preprint.repository.site_url(
            path=reverse(
                "repository_file_download",
                kwargs={
                    "preprint_id": obj.preprint.pk,
                    "file_id": obj.pk,
                },
            )
        )


class PreprintFileSerializer(PreprintFileCreateSerializer):
    class Meta:
        model = repository_models.PreprintFile
        fields = (
            "pk",
            "preprint",
            "original_filename",
            "mime_type",
            "public_download_url",
            "manager_download_url",
        )


class PreprintVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.PreprintVersion
        fields = (
            "version",
            "date_time",
            "title",
            "abstract",
            "public_download_url",
        )


class PreprintSupplementaryFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.PreprintSupplementaryFile
        fields = (
            "url",
            "label",
        )


class IssueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = journal_models.Issue
        fields = (
            "pk",
            "volume",
            "issue",
            "issue_title",
            "date",
            "issue_type",
            "issue_description",
            "cover_image",
            "large_image",
            "articles",
        )

    issue_type = serializers.ReadOnlyField(
        read_only=True,
        source="issue_type.code",
    )


class JournalSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = journal_models.Journal
        fields = (
            "pk",
            "code",
            "name",
            "publisher",
            "issn",
            "description",
            "current_issue",
            "default_cover_image",
            "default_large_image",
            "issues",
        )

    issues = serializers.HyperlinkedRelatedField(
        many=True,
        source="issue_set",
        read_only=True,
        view_name="issue-detail",
    )


class RoleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = core_models.Role
        fields = (
            "pk",
            "slug",
        )


class AccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = core_models.Account
        fields = (
            "pk",
            "email",
            "first_name",
            "middle_name",
            "last_name",
            "salutation",
            "suffix",
            "orcid",
            "is_active",
        )


class PreprintAuthorSerializer(serializers.Serializer):
    """
    A preprint author (submission.models.FrozenAuthor). Keeps the field
    names of the account-based serializer it replaced; pk is the pk of the
    linked account, if there is one, and salutation is the name prefix
    shown before the author's name. ORCIDs are accepted as an iD or URL
    and returned as an iD. An author needs an email address or a name.
    """

    pk = serializers.SerializerMethodField()
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    first_name = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        validators=[plain_text_validator],
    )
    middle_name = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[plain_text_validator],
    )
    last_name = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        validators=[plain_text_validator],
    )
    salutation = serializers.CharField(
        source="name_prefix",
        max_length=300,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[plain_text_validator],
    )
    suffix = serializers.CharField(
        source="name_suffix",
        max_length=300,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[plain_text_validator],
    )
    orcid = serializers.CharField(
        source="orcid_id",
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    institution = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    def get_pk(self, obj):
        return obj.author.pk if obj.author else None

    def validate(self, data):
        if not (
            data.get("email")
            or data.get("first_name")
            or data.get("last_name")
            or data.get("institution")
        ):
            raise serializers.ValidationError(
                "An author needs an email address, a name or an institution."
            )
        return data

    def validate_orcid(self, value):
        if not value:
            return value
        match = orcid_utils.COMPILED_ORCID_REGEX.search(value)
        if not match:
            raise serializers.ValidationError(f"{value} is not a valid ORCID")
        return match.group(0)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["orcid"] = data["orcid"] or None
        return data


def author_rows(validated_authors):
    """
    Converts validated PreprintAuthorSerializer data to the detail dicts
    the repository author logic takes.
    """
    rows = []
    for author in validated_authors:
        details = dict(author)
        if "orcid_id" in details:
            details["orcid"] = details.pop("orcid_id") or ""
        if "institution" in details:
            details["affiliation"] = details.pop("institution") or ""
        rows.append(details)
    return rows


def validate_unique_author_emails(authors):
    emails = [author["email"].lower() for author in authors if author.get("email")]
    if len(emails) != len(set(emails)):
        raise serializers.ValidationError(
            {"authors": "Each author needs a different email address."}
        )


class AccountRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_models.AccountRole
        fields = ("pk", "journal", "user", "role")

    def validate(self, data):
        request = self.context.get("request", None)
        role = data.get("role")

        excluded_roles = ["reader"]

        # if the current user is not staff add the journal-manager role to
        # the list of excluded roles.
        if not request or not request.user.is_staff:
            excluded_roles.append("journal-manager")

        if role.slug in excluded_roles:
            raise serializers.ValidationError(
                {"error": "You cannot add a user to that role via the API."}
            )

        return data


class RepositoryFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.RepositoryField
        fields = [
            "pk",
            "name",
        ]


class RepositoryFieldAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.RepositoryFieldAnswer
        fields = ["pk", "answer", "field"]

    field = RepositoryFieldSerializer(
        many=False,
    )


class PreprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.Preprint
        fields = (
            "pk",
            "title",
            "abstract",
            "stage",
            "license",
            "keywords",
            "date_submitted",
            "date_accepted",
            "date_published",
            "doi",
            "preprint_doi",
            "authors",
            "subject",
            "versions",
            "supplementary_files",
            "additional_field_answers",
            "owner",
        )
        depth = 2

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    authors = PreprintAuthorSerializer(
        source="frozen_authors",
        many=True,
    )
    license = LicenceSerializer()
    keywords = KeywordsSerializer(
        many=True,
        read_only=True,
    )
    subject = PreprintSubjectSerializer(
        many=True,
        read_only=True,
    )
    supplementary_files = PreprintSupplementaryFileSerializer(
        source="preprintsupplementaryfile_set",
        many=True,
        read_only=True,
    )
    versions = PreprintVersionSerializer(
        source="preprintversion_set",
        many=True,
        read_only=True,
    )
    additional_field_answers = RepositoryFieldAnswerSerializer(
        source="repositoryfieldanswer_set",
        many=True,
        read_only=True,
    )


class PreprintCreateSerializer(serializers.ModelSerializer):
    def validate(self, data):
        authors = data.get("frozen_authors")
        if authors is not None:
            validate_unique_author_emails(authors)

        request = self.context.get("request")
        preprint = self.instance
        moderated = (
            preprint
            and preprint.date_submitted
            and request
            and not request.user.is_staff
            and not request.user.is_repository_manager(preprint.repository)
        )
        if moderated:
            # Once submitted, owners change authors and custom fields through
            # a moderated update, and cannot unsubmit to get round that.
            errors = {}
            if "date_submitted" in data and not data["date_submitted"]:
                errors["date_submitted"] = "A submitted preprint cannot be unsubmitted."
            if authors is not None and repository_logic.PreprintAuthorList(
                preprint
            ).differs_from(author_rows(authors)):
                errors["authors"] = (
                    "The authors of a submitted preprint can only be changed "
                    "by submitting an update."
                )
            answers = data.get("repositoryfieldanswer_set")
            if answers is not None and self.answers_differ(preprint, answers):
                errors["additional_field_answers"] = (
                    "The additional information of a submitted preprint can "
                    "only be changed by submitting an update."
                )
            if errors:
                raise serializers.ValidationError(errors)
        return data

    @staticmethod
    def answers_differ(preprint, answers):
        current = {
            answer.field.name: answer.answer
            for answer in preprint.repositoryfieldanswer_set.select_related("field")
            if answer.field
        }
        proposed = {
            answer.get("field", {}).get("name"): answer.get("answer")
            for answer in answers
            if answer.get("field", {}).get("name") and answer.get("answer")
        }
        return current != proposed

    @transaction.atomic
    def create(self, validated_data):
        preprint = repository_models.Preprint.objects.create(
            repository=validated_data.get("repository"),
            title=validated_data.get("title"),
            abstract=validated_data.get("abstract"),
            owner=validated_data.get("owner"),
            stage=validated_data.get("stage", "preprint_review"),
            license=validated_data.get("license"),
            date_submitted=validated_data.get("date_submitted"),
            date_accepted=validated_data.get("date_accepted"),
            date_published=validated_data.get("date_published"),
            doi=validated_data.get("doi"),
            preprint_doi=validated_data.get("preprint_doi"),
            comments_editor=validated_data.get("comments_editor"),
        )

        if "frozen_authors" in validated_data:
            repository_logic.PreprintAuthorList(preprint).replace(
                author_rows(validated_data["frozen_authors"]),
                editor=self.context["request"].user,
            )

        for keywords in validated_data.get("keywords", []):
            for key, word in keywords.items():
                if word and word not in ["", " "]:
                    kwd, c = submission_models.Keyword.objects.get_or_create(word=word)
                    preprint.keywords.add(kwd)

        for subjects in validated_data.get("subject", []):
            for key, subject in subjects.items():
                if subject not in ["", " "]:
                    subject_obj, c = repository_models.Subject.objects.get_or_create(
                        name=subject,
                        repository=preprint.repository,
                    )
                    preprint.subject.add(subject_obj)

        for fieldanswers in validated_data.get("repositoryfieldanswer_set", []):
            answer = fieldanswers.get("answer")
            field = fieldanswers.get("field").get("name")

            if field and answer:
                field_obj, c = repository_models.RepositoryField.objects.get_or_create(
                    name=field,
                    repository=preprint.repository,
                    defaults={
                        "order": 0,
                        "input_type": "textarea",
                        "required": False,
                    },
                )
                repository_models.RepositoryFieldAnswer.objects.get_or_create(
                    field=field_obj,
                    answer=answer,
                    preprint=preprint,
                )
        for supp_file in validated_data.get("preprintsupplementaryfile_set"):
            url = supp_file.get("url")
            label = supp_file.get("label")

            if url and label:
                repository_models.PreprintSupplementaryFile.objects.update_or_create(
                    preprint=preprint,
                    url=url,
                    defaults={
                        "label": label,
                    },
                )

        return preprint

    @transaction.atomic
    def update(self, instance, validated_data):
        pre_save_stage = instance.stage

        # Before submitting, while the owner can still edit the authors.
        if "frozen_authors" in validated_data:
            repository_logic.PreprintAuthorList(instance).replace(
                author_rows(validated_data["frozen_authors"]),
                editor=self.context["request"].user,
            )

        if (
            pre_save_stage == repository_models.STAGE_PREPRINT_UNSUBMITTED
            and validated_data.get("stage") == repository_models.STAGE_PREPRINT_REVIEW
        ):
            request = self.context.get("request", None)
            instance.submit_preprint()
            kwargs = {"request": request, "preprint": instance}
            event_logic.Events.raise_event(
                event_logic.Events.ON_PREPRINT_SUBMISSION,
                **kwargs,
            )

        instance.title = validated_data.get("title")
        instance.abstract = validated_data.get("abstract")
        instance.owner = validated_data.get("owner")
        instance.repository = validated_data.get("repository")
        instance.stage = validated_data.get("stage")
        instance.license = validated_data.get("license")
        instance.date_submitted = validated_data.get(
            "date_submitted",
            instance.date_submitted,
        )
        instance.date_accepted = validated_data.get("date_accepted")
        instance.date_published = validated_data.get("date_published")
        instance.doi = validated_data.get("doi")
        instance.preprint_doi = validated_data.get("preprint_doi")
        instance.comments_editor = validated_data.get("comments_editor")
        instance.save()

        # Remove all keywords and add those present back.
        instance.keywords.clear()
        for keywords in validated_data.get("keywords", []):
            for key, word in keywords.items():
                if word and word not in ["", " "]:
                    kwd, c = submission_models.Keyword.objects.get_or_create(word=word)
                    instance.keywords.add(kwd)
        # Remove all subjects and add those present back.
        instance.subject.clear()
        for subjects in validated_data.get("subject", []):
            for key, subject in subjects.items():
                if subject not in ["", " "]:
                    subject_obj, c = repository_models.Subject.objects.get_or_create(
                        name=subject,
                        repository=instance.repository,
                    )
                    instance.subject.add(subject_obj)

        answers = []
        for fieldanswers in validated_data.get("repositoryfieldanswer_set", []):
            answer = fieldanswers.get("answer")
            field = fieldanswers.get("field").get("name")
            if field and answer:
                field_obj, c = repository_models.RepositoryField.objects.get_or_create(
                    name=field,
                    repository=instance.repository,
                    defaults={
                        "order": 0,
                        "input_type": "textarea",
                        "required": False,
                    },
                )
                answer, c = (
                    repository_models.RepositoryFieldAnswer.objects.update_or_create(
                        field=field_obj,
                        answer=answer,
                        preprint=instance,
                    )
                )
                answers.append(answer)

        # Remove answers not part of the update.
        for answer_obj in instance.repositoryfieldanswer_set.all():
            if answer_obj not in answers:
                answer_obj.delete()

        urls = []
        for supp_file in validated_data.get("preprintsupplementaryfile_set"):
            url = supp_file.get("url")
            label = supp_file.get("label")

            if url and label:
                repository_models.PreprintSupplementaryFile.objects.update_or_create(
                    preprint=instance,
                    url=url,
                    defaults={
                        "label": label,
                    },
                )
                urls.append(url)
        for supp_file in instance.preprintsupplementaryfile_set.all():
            if supp_file.url not in urls:
                supp_file.delete()

        return instance

    class Meta:
        model = repository_models.Preprint
        fields = (
            "pk",
            "authors",
            "title",
            "abstract",
            "stage",
            "license",
            "keywords",
            "date_submitted",
            "date_accepted",
            "date_published",
            "doi",
            "preprint_doi",
            "subject",
            "additional_field_answers",
            "owner",
            "repository",
            "supplementary_files",
            "comments_editor",
        )

    authors = PreprintAuthorSerializer(
        source="frozen_authors",
        many=True,
        required=False,
    )
    keywords = KeywordsSerializer(
        many=True,
    )
    subject = PreprintSubjectSerializer(
        many=True,
    )
    additional_field_answers = RepositoryFieldAnswerSerializer(
        source="repositoryfieldanswer_set",
        many=True,
    )
    supplementary_files = PreprintSupplementaryFileSerializer(
        source="preprintsupplementaryfile_set",
        many=True,
    )


class UserPreprintSerializer(PreprintCreateSerializer):
    """
    Creates and updates a user's own preprints. Owners can only submit them:
    moderators decide the stage, dates and DOI, and submitted preprints change
    through new versions.
    """

    OWNER_STAGES = (
        repository_models.STAGE_PREPRINT_UNSUBMITTED,
        repository_models.STAGE_PREPRINT_REVIEW,
    )

    def validate(self, attrs):
        request = self.context["request"]
        if self.instance and self.instance.date_submitted:
            raise exceptions.PermissionDenied(
                "Submitted preprints can only be changed by submitting a new version."
            )
        attrs = super().validate(attrs)

        default_stage = (
            repository_models.STAGE_PREPRINT_UNSUBMITTED
            if self.instance
            else repository_models.STAGE_PREPRINT_REVIEW
        )
        stage = attrs.get("stage") or default_stage
        if stage not in self.OWNER_STAGES:
            raise serializers.ValidationError(
                {"stage": f"Choose one of: {', '.join(self.OWNER_STAGES)}."}
            )

        submitted = stage == repository_models.STAGE_PREPRINT_REVIEW
        attrs.update(
            stage=stage,
            owner=request.user,
            repository=request.repository,
            date_submitted=timezone.now() if submitted else None,
            date_accepted=None,
            date_published=None,
            preprint_doi=None,
        )
        return attrs


class SubmissionAccountSearch(serializers.ModelSerializer):
    class Meta:
        model = core_models.Account
        fields = (
            "pk",
            "first_name",
            "middle_name",
            "last_name",
            "orcid",
            "email",
        )


class ProposedFieldAnswerSerializer(serializers.Serializer):
    """
    A custom field answer proposed by a preprint update. The field is
    identified by name, as when creating a preprint. A blank or null answer
    clears the field.
    """

    field = RepositoryFieldSerializer()
    answer = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )


class VersionQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.VersionQueue
        fields = (
            "pk",
            "preprint",
            "update_type",
            "date_submitted",
            "date_decision",
            "approved",
            "published_doi",
            "title",
            "abstract",
            "file",
            "changed_sections",
            "authors_changed",
            "field_answers_changed",
            "authors",
            "additional_field_answers",
        )

    authors = PreprintAuthorSerializer(
        source="frozenauthor_set",
        many=True,
        read_only=True,
    )
    additional_field_answers = RepositoryFieldAnswerSerializer(
        source="repositoryfieldanswer_set",
        many=True,
        read_only=True,
    )


class VersionQueueCreateSerializer(serializers.ModelSerializer):
    """
    Requests an update to a submitted preprint the user owns, as the web
    form does. Besides title, abstract, DOI and file (required, except for
    a metadata correction), an update can give:

    - authors: the complete new author list, in order. Authors already on
      the preprint are matched by email address, or by name when there is
      none, and keep their account link, affiliations and CRediT roles.
      Omit it to keep the current list.
    - additional_field_answers: answers to the repository's custom fields,
      by field name. Fields not listed keep their current answer.

    A preprint has one open update at a time. A moderator applies the
    sections that differ from the preprint by approving the update.
    """

    authors = PreprintAuthorSerializer(
        many=True,
        required=False,
        write_only=True,
    )
    additional_field_answers = ProposedFieldAnswerSerializer(
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = repository_models.VersionQueue
        fields = (
            "preprint",
            "update_type",
            "title",
            "abstract",
            "published_doi",
            "file",
            "authors",
            "additional_field_answers",
        )

    def validate(self, data):
        request = self.context.get("request", None)
        preprint = data.get("preprint")

        if not request.user == preprint.owner:
            raise serializers.ValidationError(
                {
                    "error": "You cannot add a version for a preprint "
                    "that you do not own."
                }
            )
        if preprint.repository != getattr(request, "repository", preprint.repository):
            raise serializers.ValidationError(
                {"preprint": "This preprint does not belong to this repository."}
            )
        if preprint.stage not in repository_models.SUBMITTED_STAGES:
            raise serializers.ValidationError(
                {"preprint": "Only submitted preprints can be updated."}
            )
        open_update = repository_logic.open_update(preprint)
        if open_update and open_update.is_draft:
            raise serializers.ValidationError(
                {
                    "preprint": "This preprint has a draft update on the "
                    "website. Submit or discard it there first."
                }
            )
        if open_update:
            raise serializers.ValidationError(
                {"preprint": "This preprint already has an update awaiting moderation."}
            )
        update_file = data.get("file")
        if data.get("update_type") == "metadata_correction":
            if update_file:
                raise serializers.ValidationError(
                    {"file": "A metadata correction cannot change the file."}
                )
        elif not update_file:
            raise serializers.ValidationError(
                {"file": "A correction or new version needs a file."}
            )
        if update_file and update_file.preprint_id != preprint.pk:
            raise serializers.ValidationError(
                {"file": "This file does not belong to this preprint."}
            )

        authors = data.get("authors")
        if authors is not None:
            if not authors:
                raise serializers.ValidationError(
                    {"authors": "You must list at least one author."}
                )
            validate_unique_author_emails(authors)

        answers = data.get("additional_field_answers")
        if answers is not None:
            available = {
                field.name: field
                for field in preprint.repository.type_additional_submission_fields(
                    submission_type_slug=(
                        preprint.submission_type.slug
                        if preprint.submission_type
                        else None
                    ),
                )
            }
            resolved = {}
            for answer in answers:
                name = answer["field"]["name"]
                field = available.get(name)
                if field is None:
                    raise serializers.ValidationError(
                        {"additional_field_answers": f"Unknown field: {name}"}
                    )
                if field in resolved:
                    raise serializers.ValidationError(
                        {"additional_field_answers": f"Field listed twice: {name}"}
                    )
                resolved[field] = self.clean_field_answer(field, answer.get("answer"))
            data["additional_field_answers"] = resolved

        return data

    @staticmethod
    def clean_field_answer(field, value):
        """
        Validates a proposed answer as the web form would.
        :return: the answer text, or None to clear the field
        """
        if value in (None, ""):
            if field.required:
                raise serializers.ValidationError(
                    {"additional_field_answers": f"{field.name} is required."}
                )
            return None
        form_field = repository_forms.build_additional_field(field)
        try:
            cleaned = form_field.clean(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {
                    "additional_field_answers": f"{field.name}: {' '.join(error.messages)}"
                }
            )
        return repository_forms.additional_field_answer_text(field, cleaned)

    @transaction.atomic
    def create(self, validated_data):
        authors = validated_data.pop("authors", None)
        answers = validated_data.pop("additional_field_answers", None)
        version_queue, error = repository_logic.start_update(
            validated_data.pop("preprint"),
            validated_data.pop("update_type"),
        )
        if error:
            raise serializers.ValidationError({"preprint": str(error)})
        for name, value in validated_data.items():
            setattr(version_queue, name, value)
        version_queue.save()
        if authors is not None:
            repository_logic.PreprintAuthorList(
                version_queue.preprint,
                version_queue,
            ).replace(author_rows(authors), editor=self.context["request"].user)
        if answers:
            repository_logic.set_update_field_answers(version_queue, answers)
        error = repository_logic.submit_update(version_queue)
        if error:
            raise serializers.ValidationError({"error": str(error)})
        version_queue.refresh_from_db()

        # Notify moderators as the web form does, once the update is saved.
        request = self.context.get("request")

        def notify():
            try:
                event_logic.Events.raise_event(
                    event_logic.Events.ON_PREPRINT_NEW_VERSION,
                    request=request,
                    new_version=version_queue,
                    preprint=version_queue.preprint,
                )
            except Exception:
                # The update is saved; a failed notification must not turn
                # the response into an error.
                logger.exception("Could not notify moderators of a new version")

        transaction.on_commit(notify)

        return version_queue

    def to_representation(self, instance):
        return VersionQueueSerializer(instance, context=self.context).data


class RegisterAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_models.Account
        fields = (
            "pk",
            "email",
            "salutation",
            "first_name",
            "middle_name",
            "last_name",
            "orcid",
            "institution",
            "department",
            "biography",
            "password",
            "confirmation_code",
        )

    def create(self, validated_data):
        user = super().create(validated_data)
        password = validated_data.get("password")
        if password:
            user.set_password(password)

        user.confirmation_code = uuid.uuid4()
        user.save()

        request = self.context.get("request")
        if request:
            core_logic.send_confirmation_link(request, user)

        return user

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        try:
            if validated_data.get("password"):
                user.set_password(validated_data["password"])
                user.save()
        except KeyError:
            pass
        return user

    password = serializers.CharField(
        max_length=128,
        write_only=True,
        required=False,
    )
    confirmation_code = serializers.CharField(
        read_only=True,
    )


class ActivateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_models.Account
        fields = ("confirmation_code",)

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        user.is_active = True
        user.save()
        return user

    confirmation_code = serializers.CharField(
        read_only=True,
    )


class IdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = identifier_models.Identifier
        fields = (
            "id_type",
            "identifier",
            "article",
            "preprint_version",
        )

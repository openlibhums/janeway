import uuid

from rest_framework import serializers, validators

from django.conf import settings
from django.db import transaction
from django.shortcuts import reverse
from modeltranslation.utils import build_localized_fieldname

from core import models as core_models, logic as core_logic
from journal import models as journal_models
from submission import models as submission_models
from repository import models as repository_models
from identifiers import models as identifier_models
from events import logic as event_logic


def translatable_repository(instance):
    """Return the repository governing the active languages for a translatable
    preprint object (Preprint, PreprintVersion or VersionQueue)."""
    if hasattr(instance, "repository"):
        return instance.repository
    return instance.preprint.repository


def apply_translations(instance, field_name, translations):
    """Set per-language values for a modeltranslation-managed field from a
    ``{language_code: value}`` mapping. Does not save the instance."""
    if not translations:
        return
    for code, value in translations.items():
        setattr(instance, build_localized_fieldname(field_name, code), value)


class TranslationsField(serializers.DictField):
    """A readable and writable ``{language_code: value}`` map for a
    modeltranslation-managed field. On read it exposes one entry per language
    the preprint's repository accepts; on write it accepts a partial mapping."""

    def __init__(self, translated_field, **kwargs):
        self.translated_field = translated_field
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "child",
            serializers.CharField(allow_blank=True, trim_whitespace=False),
        )
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        # to_representation builds the map from the instance itself.
        return instance

    def to_representation(self, instance):
        repository = translatable_repository(instance)
        languages = repository.languages or [settings.LANGUAGE_CODE]
        return {
            code: getattr(
                instance,
                build_localized_fieldname(self.translated_field, code),
                "",
            )
            or ""
            for code in languages
        }


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
            "title_translations",
            "abstract_translations",
            "public_download_url",
        )

    title_translations = TranslationsField("title", read_only=True)
    abstract_translations = TranslationsField("abstract", read_only=True)


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


class PreprintAccountSerializer(serializers.HyperlinkedModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        if "email" in fields:
            fields["email"].validators = [
                validator
                for validator in fields["email"].validators
                if not isinstance(validator, validators.UniqueValidator)
            ]
        return fields

    def create(self, validated_data):
        account_email = validated_data.pop("email")
        account, created = core_models.Account.objects.get_or_create(
            email=account_email,
            defaults={
                **validated_data,
            },
        )
        return account

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
            "institution",
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
            "title_translations",
            "abstract_translations",
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

    title_translations = TranslationsField("title", read_only=True)
    abstract_translations = TranslationsField("abstract", read_only=True)
    authors = PreprintAccountSerializer(
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

        apply_translations(preprint, "title", validated_data.get("title_translations"))
        apply_translations(
            preprint, "abstract", validated_data.get("abstract_translations")
        )
        if validated_data.get("title_translations") or validated_data.get(
            "abstract_translations"
        ):
            preprint.save()

        for i, author_data in enumerate(validated_data.get("authors", [])):
            author_email = author_data.pop("email").lower()
            author, created = core_models.Account.objects.get_or_create(
                email=author_email,
                defaults={
                    **author_data,
                },
            )
            repository_models.PreprintAuthor.objects.get_or_create(
                account=author,
                preprint=preprint,
                defaults={
                    "order": i,
                    "affiliation": author.affiliation(),
                },
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
        instance.date_submitted = validated_data.get("date_submitted")
        instance.date_accepted = validated_data.get("date_accepted")
        instance.date_published = validated_data.get("date_published")
        instance.doi = validated_data.get("doi")
        instance.preprint_doi = validated_data.get("preprint_doi")
        instance.comments_editor = validated_data.get("comments_editor")
        apply_translations(instance, "title", validated_data.get("title_translations"))
        apply_translations(
            instance, "abstract", validated_data.get("abstract_translations")
        )
        instance.save()

        authors = []
        for i, author_data in enumerate(validated_data.get("authors", [])):
            author_email = author_data.pop("email").lower()
            # check if there is an existing PreprintAuthor record and update it
            account, created = core_models.Account.objects.update_or_create(
                email=author_email,
                defaults={
                    **author_data,
                },
            )
            preprint_author, c = (
                repository_models.PreprintAuthor.objects.update_or_create(
                    account=account,
                    preprint=instance,
                    defaults={
                        "order": i,
                        "affiliation": author_data.get("institution"),
                    },
                )
            )
            authors.append(preprint_author)

        # Delete any authors not present in the list of authors
        # that were found/created above.
        for preprint_author in instance.preprintauthor_set.all():
            if preprint_author not in authors:
                preprint_author.delete()

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
            "title_translations",
            "abstract_translations",
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

    title_translations = TranslationsField("title")
    abstract_translations = TranslationsField("abstract")
    authors = PreprintAccountSerializer(
        many=True,
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


class VersionQueueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.VersionQueue
        fields = (
            "preprint",
            "update_type",
            "title",
            "abstract",
            "title_translations",
            "abstract_translations",
            "published_doi",
            "file",
        )

    title_translations = TranslationsField("title")
    abstract_translations = TranslationsField("abstract")

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

        return data

    def create(self, validated_data):
        title_translations = validated_data.pop("title_translations", None)
        abstract_translations = validated_data.pop("abstract_translations", None)
        version_queue = super().create(validated_data)
        apply_translations(version_queue, "title", title_translations)
        apply_translations(version_queue, "abstract", abstract_translations)
        if title_translations or abstract_translations:
            version_queue.save()
        return version_queue


class VersionQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.VersionQueue
        fields = (
            "preprint",
            "update_type",
            "date_submitted",
            "date_decision",
            "approved",
            "published_doi",
            "title",
            "abstract",
            "title_translations",
            "abstract_translations",
            "file",
        )

    title_translations = TranslationsField("title", read_only=True)
    abstract_translations = TranslationsField("abstract", read_only=True)


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

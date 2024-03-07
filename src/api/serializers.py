from rest_framework import serializers, validators
from rest_framework.exceptions import ValidationError

from django.db import transaction

from core import models as core_models
from journal import models as journal_models
from submission import models as submission_models
from repository import models as repository_models


class LicenceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = submission_models.Licence
        fields = ('pk', 'name', 'short_name', 'text', 'url')


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
            word=validated_data.get('word'),
        )
        return keyword

    class Meta:
        model = submission_models.Keyword
        fields = ('word',)


class FrozenAuthorSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = submission_models.FrozenAuthor
        fields = (
            'first_name',
            'middle_name',
            'last_name',
            'name_suffix',
            'institution',
            'department',
            'country',
        )

    country = serializers.ReadOnlyField(
        read_only=True,
        source="country.name",
    )


class GalleySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = core_models.Galley
        fields = ('label', 'type', 'path')


class ArticleSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = submission_models.Article
        fields = ('pk', 'title', 'subtitle', 'abstract', 'language', 'license', 'keywords', 'section',
                  'is_remote', 'remote_url', 'frozenauthors', 'date_submitted', 'date_accepted',
                  'date_published', 'render_galley', 'galleys')

    license = LicenceSerializer()
    keywords = KeywordsSerializer(
        many=True,
        read_only=True,
    )
    section = serializers.ReadOnlyField(
        read_only=True,
        source='section.name'
    )
    frozenauthors = FrozenAuthorSerializer(
        many=True,
        source='frozenauthor_set',
    )
    render_galley = GalleySerializer(
        read_only=True,
    )
    galleys = GalleySerializer(
        source='galley_set',
        many=True
    )


class PreprintSubjectSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = repository_models.Subject
        fields = ('name',)


class PreprintFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = repository_models.PreprintFile
        fields = ('original_filename', 'mime_type', 'download_url',)


class PreprintVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = repository_models.PreprintVersion
        fields = (
            'version',
            'date_time',
            'title',
            'abstract',
            'public_download_url',
        )


class PreprintSupplementaryFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = repository_models.PreprintSupplementaryFile
        fields = ('url', 'label',)


class IssueSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = journal_models.Issue
        fields = ('pk', 'volume', 'issue', 'issue_title', 'date', 'issue_type', 'issue_description',
                  'cover_image', 'large_image', 'articles')

    issue_type = serializers.ReadOnlyField(
        read_only=True,
        source="issue_type.code",
    )


class JournalSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = journal_models.Journal
        fields = ('pk', 'code', 'name', 'publisher', 'issn', 'description', 'current_issue', 'default_cover_image',
                  'default_large_image', 'issues')

    issues = serializers.HyperlinkedRelatedField(
        many=True,
        source='issue_set',
        read_only=True,
        view_name='issue-detail',
    )


class RoleSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = core_models.Role
        fields = ('pk', 'slug',)


class AccountSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = core_models.Account
        fields = (
            'pk', 'email', 'first_name', 'middle_name', 'last_name',
            'salutation', 'orcid', 'is_active',
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
        account_email = validated_data.pop('email')
        account, created = core_models.Account.objects.get_or_create(
            email=account_email,
            defaults={
                **validated_data,
            }
        )
        return account

    class Meta:
        model = core_models.Account
        fields = (
            'pk', 'email', 'first_name', 'middle_name', 'last_name',
            'salutation', 'orcid', 'institution',
        )


class AccountRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = core_models.AccountRole
        fields = ('pk', 'journal', 'user', 'role')

    def create(self, validated_data):
        role = validated_data.get("role")

        if role.slug == 'reader':
            raise serializers.ValidationError(
                {"role": "You cannot add a user as a reader via the API."}
            )
        else:
            account_role = core_models.AccountRole.objects.create(**validated_data)
            return account_role

    def validate(self, data):
        request = self.context.get('request', None)
        role = data.get("role")

        excluded_roles = ['reader']

        # if the current user is not staff add the journal-manager role to
        # the list of excluded roles.
        if not request or not request.user.is_staff:
            excluded_roles.append('journal-manager')

        if role.slug in excluded_roles:
            raise serializers.ValidationError(
                {"error": "You cannot add a user to that role via the API."}
            )

        return data


class RepositoryFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.RepositoryField
        fields = ['pk', 'name',]


class RepositoryFieldAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.RepositoryFieldAnswer
        fields = ['pk', 'answer', 'field']

    field = RepositoryFieldSerializer(
        many=False,
    )


class PreprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.Preprint
        fields = ('pk', 'title', 'abstract', 'stage', 'license', 'keywords',
                  'date_submitted', 'date_accepted', 'date_published',
                  'doi', 'preprint_doi', 'authors', 'subject', 'versions',
                  'supplementary_files', 'additional_field_answers', 'owner')

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
            repository=validated_data.get('repository'),
            title=validated_data.get('title'),
            abstract=validated_data.get('abstract'),
            owner=validated_data.get('owner'),
            stage=validated_data.get('stage'),
            license=validated_data.get('license'),
            date_submitted=validated_data.get('date_submitted'),
            date_accepted=validated_data.get('date_accepted'),
            date_published=validated_data.get('date_published'),
            doi=validated_data.get('doi'),
            preprint_doi=validated_data.get('preprint_doi'),
        )

        for i, author_data in enumerate(validated_data.get('authors', [])):
            author_email = author_data.pop('email').lower()
            author, created = core_models.Account.objects.get_or_create(
                email=author_email,
                defaults={
                    **author_data,
                }
            )
            repository_models.PreprintAuthor.objects.get_or_create(
                account=author,
                preprint=preprint,
                defaults={
                    'order': i,
                    'affiliation': author.affiliation(),
                }
            )

        for keywords in validated_data.get('keywords', []):
            for key, word in keywords.items():
                if word and word not in ['', ' ']:
                    kwd, c = submission_models.Keyword.objects.get_or_create(
                        word=word
                    )
                    preprint.keywords.add(kwd)

        for subjects in validated_data.get('subject', []):
            for key, subject in subjects.items():
                if subject not in ['', ' ']:
                    subject_obj, c = repository_models.Subject.objects.get_or_create(
                        name=subject,
                        repository=preprint.repository,
                    )
                    preprint.subject.add(subject_obj)

        for fieldanswers in validated_data.get('repositoryfieldanswer_set', []):
            answer = fieldanswers.get('answer')
            field = fieldanswers.get('field').get('name')

            if field and answer:
                field_obj, c = repository_models.RepositoryField.objects.get_or_create(
                    name=field,
                    repository=preprint.repository,
                    defaults={
                        'order': 0,
                        'input_type': 'textarea',
                        'required': False,
                    }
                )
                repository_models.RepositoryFieldAnswer.objects.get_or_create(
                    field=field_obj,
                    answer=answer,
                    preprint=preprint,
                )

        return preprint

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.title = validated_data.get('title')
        instance.abstract = validated_data.get('abstract')
        instance.owner = validated_data.get('owner')
        instance.repository = validated_data.get('repository')
        instance.stage = validated_data.get('stage')
        instance.license = validated_data.get('license')
        instance.date_submitted = validated_data.get('date_submitted')
        instance.date_accepted = validated_data.get('date_accepted')
        instance.date_published = validated_data.get('date_published')
        instance.doi = validated_data.get('doi')
        instance.preprint_doi = validated_data.get('preprint_doi')
        instance.save()

        authors = []
        for i, author_data in enumerate(validated_data.get('authors', [])):
            author_email = author_data.pop('email').lower()
            # check if there is an existing PreprintAuthor record and update it
            account, created = core_models.Account.objects.update_or_create(
                email=author_email,
                defaults={
                    **author_data,
                }
            )
            preprint_author, c = repository_models.PreprintAuthor.objects.update_or_create(
                account=account,
                preprint=instance,
                defaults={
                    'order': i,
                    'affiliation': author_data.get('institution'),
                }
            )
            authors.append(preprint_author)

        # Delete any authors not present in the list of authors
        # that were found/created above.
        for preprint_author in instance.preprintauthor_set.all():
            if preprint_author not in authors:
                preprint_author.delete()

        # Remove all keywords and add those present back.
        instance.keywords.clear()
        for keywords in validated_data.get('keywords', []):
            for key, word in keywords.items():
                if word and word not in ['', ' ']:
                    kwd, c = submission_models.Keyword.objects.get_or_create(
                        word=word
                    )
                    instance.keywords.add(kwd)
        # Remove all subjects and add those present back.
        instance.subject.clear()
        for subjects in validated_data.get('subject', []):
            for key, subject in subjects.items():
                if subject not in ['', ' ']:
                    subject_obj, c = repository_models.Subject.objects.get_or_create(
                        name=subject,
                        repository=instance.repository,
                    )
                    instance.subject.add(subject_obj)

        answers = []
        for fieldanswers in validated_data.get('repositoryfieldanswer_set', []):
            answer = fieldanswers.get('answer')
            field = fieldanswers.get('field').get('name')
            if field and answer:
                field_obj, c = repository_models.RepositoryField.objects.get_or_create(
                    name=field,
                    repository=instance.repository,
                    defaults={
                        'order': 0,
                        'input_type': 'textarea',
                        'required': False,
                    }
                )
                answer, c = repository_models.RepositoryFieldAnswer.objects.update_or_create(
                    field=field_obj,
                    answer=answer,
                    preprint=instance,
                )
                answers.append(answer)

        # Remove answers not part of the update.
        for answer_obj in instance.repositoryfieldanswer_set.all():
            if answer_obj not in answers:
                answer_obj.delete()

        return instance

    class Meta:
        model = repository_models.Preprint
        fields = ('pk', 'authors', 'title', 'abstract', 'stage', 'license', 'keywords',
                  'date_submitted', 'date_accepted', 'date_published',
                  'doi', 'preprint_doi', 'subject',
                  'additional_field_answers', 'owner', 'repository')

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
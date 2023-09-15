from rest_framework import serializers

from core import models as core_models
from journal import models as journal_models
from submission import models as submission_models
from repository import models as repository_models


class LicenceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = submission_models.Licence
        fields = ('name', 'short_name', 'text', 'url')


class KeywordsSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = submission_models.Keyword
        fields = ('word',)


class FrozenAuthorSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = submission_models.FrozenAuthor
        fields = ('first_name', 'middle_name', 'last_name', 'name_suffix', 'institution', 'department', 'country')

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

    class Meta:
        model = core_models.Account
        fields = (
            'pk', 'first_name', 'middle_name', 'last_name',
            'salutation', 'orcid',
        )

class AccountRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = core_models.AccountRole
        fields = ('pk', 'journal', 'user', 'role')

    def create(self, validated_data):
        role = validated_data.get("role")

        if role.slug == 'reader':
            raise serializers.ValidationError({"role": "You cannot add a user as a reader via the API."})
        else:
            account_role = core_models.AccountRole.objects.create(**validated_data)
            return account_role

class RepositoryFieldAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = repository_models.RepositoryFieldAnswer
        fields = ['pk', 'answer']

class PreprintSerializer(serializers.ModelSerializer):

    class Meta:
        model = repository_models.Preprint
        fields = ('pk', 'title', 'abstract', 'license', 'keywords', 
                  'date_submitted', 'date_accepted', 'date_published',
                  'doi', 'preprint_doi', 'authors', 'subject', 'files', 'supplementary_files')
        depth = 2

    authors = PreprintAccountSerializer(
        many=True,
        read_only=True,
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
    files = PreprintFileSerializer(
        source="preprintfile_set",
        many=True,
        read_only=True,
    )
    supplementary_files = PreprintSupplementaryFileSerializer(
        source="preprintsupplementaryfile_set",
        many=True,
        read_only=True,
    )
    def validate(self, data):
        request = self.context.get('request', None)
        role = data.get("role")

        excluded_roles = ['reader']

        # if the current user is not staff add the journal-manager role to
        # the list of excluded roles.
        if not request or not request.user.is_staff:
            excluded_roles.append('journal-manager')

        if role.slug in excluded_roles:
            raise serializers.ValidationError({"error": "You cannot add a user to that role via the API."})

        return data

from rest_framework import serializers

from core import models as core_models
from journal import models as journal_models
from submission import models as submission_models


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
        fields = ('first_name', 'middle_name', 'last_name', 'institution', 'department', 'country')

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


class AccountRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = core_models.AccountRole
        fields = ('pk', 'journal', 'user', 'role')

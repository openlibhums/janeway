from rest_framework import serializers

from core import models as core_models
from journal import models as journal_models


class JournalSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = journal_models.Journal
        fields = ('pk', 'code',)


class RoleSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = core_models.Role
        fields = ('pk', 'slug',)


class AccountSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = core_models.Account
        fields = ('pk', 'email',)


class AccountRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = core_models.AccountRole
        fields = ('pk', 'journal', 'user', 'role')

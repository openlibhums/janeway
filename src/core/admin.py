__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from hvad.admin import TranslatableAdmin
from django.utils.safestring import mark_safe

from core import models


class AccountRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'journal')
    list_filter = ('user', 'role', 'journal')
    raw_id_fields = ('user',)


class SettingAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('name', 'group', 'types', 'is_translatable')
    list_filter = ('group', 'types', 'is_translatable')
    search_fields = ('name',)


class AccountAdmin(UserAdmin):
    """Displays Account objects in the Django admin interface."""
    list_display = ('username', 'email', 'first_name', 'middle_name', 'last_name', 'institution', 'date_confirmed')
    search_fields = ('username', 'email', 'first_name', 'middle_name', 'last_name', 'orcid', 'institution', 'biography')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': (
            'middle_name', 'orcid', 'institution', 'department', 'twitter', 'linkedin', 'facebook', 'github',
            'biography',
            'signature', 'profile_image', 'interest')}),
    )


class RoleAdmin(admin.ModelAdmin):
    """Displays Role objects in the Django admin interface."""
    list_display = ('name',)
    search_fields = ('name',)


class PasswordResetAdmin(admin.ModelAdmin):
    """Displays Password Reset Data"""
    list_display = ('account', 'expiry', 'expired')
    search_fields = ('account',)
    list_filter = ('expired',)
    raw_id_fields = ('account',)


class SettingValueAdmin(TranslatableAdmin):
    list_display = ('setting_journal', 'setting_pretty_name')
    list_filter = ('setting', 'journal')

    @staticmethod
    def apply_select_related(self, qs):
        return qs.prefetch_related('journal', 'setting')

    def setting_journal(self, obj):
        return obj.journal

    def setting_pretty_name(self, obj):
        return obj.setting.pretty_name


class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('name', 'code')


class HomepageElementAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('name', 'object', 'sequence')
    list_filter = ('name',)
    search_fields = ('name',)


class FileAdmin(admin.ModelAdmin):
    """displays files"""
    search_fields = ('original_filename',)
    list_display = ('id', 'original_filename', 'self_article_path', 'article_pk', 'mime_type')
    list_filter = ('mime_type',)
    raw_id_fields = ('owner',)
    filter_horizontal = ('history',)

    def article_pk(self, obj):
        if obj.article:
            link = '<a href="/admin/submission/article/{pk}/change/">{pk}</a>'.format(pk=obj.article.pk)
            return mark_safe(link)
        else:
            return '-'


class WorkflowElementAdmin(admin.ModelAdmin):
    search_fields = ('element_name',)
    list_display = ('element_name', 'journal', 'handshake_url', 'stage', 'order')
    list_filter = ('journal',)


class WorkflowLogAdmin(admin.ModelAdmin):
    search_fields = ('article',)
    list_display = ('article', 'element', 'timestamp')
    list_filter = ('element',)


class OrcidTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'orcid', 'expiry')


class SettingGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled')
    list_filter = ('enabled',)


admin_list = [
    (models.AccountRole, AccountRoleAdmin),
    (models.Account, AccountAdmin),
    (models.Role, RoleAdmin,),
    (models.Setting, SettingAdmin),
    (models.SettingGroup, SettingGroupAdmin),
    (models.SettingValue, SettingValueAdmin),
    (models.File, FileAdmin),
    (models.Interest,),
    (models.Task,),
    (models.TaskCompleteEvents,),
    (models.Galley,),
    (models.EditorialGroup,),
    (models.EditorialGroupMember,),
    (models.PasswordResetToken, PasswordResetAdmin),
    (models.OrcidToken, OrcidTokenAdmin),
    (models.DomainAlias,),
    (models.Country, CountryAdmin),
    (models.WorkflowElement, WorkflowElementAdmin),
    (models.HomepageElement, HomepageElementAdmin),
    (models.WorkflowLog, WorkflowLogAdmin),
    (models.LoginAttempt,),
]

[admin.site.register(*t) for t in admin_list]

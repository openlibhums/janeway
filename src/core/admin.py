__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from core import models, forms


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
            'middle_name', 'orcid', 'institution', 'department', 'twitter',
            'linkedin', 'facebook', 'github', 'biography',
            'signature', 'profile_image', 'interest', "preferred_timezone",
        )}),
    )

    add_form = forms.UserCreationFormExtended
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name',
                       'password1', 'password2',)
        }),
    )

    raw_id_fields = ('interest',)


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


class SettingValueAdmin(admin.ModelAdmin):
    list_display = ('setting_journal', 'setting_pretty_name')
    list_filter = ('setting', 'journal')
    raw_id_fields = (
        'setting', 'journal',
    )

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
    list_filter = ('mime_type', 'article_id')
    raw_id_fields = ('owner',)
    filter_horizontal = ('history',)
    readonly_fields = ['article_id']

    def article_pk(self, obj):
        if obj.article:
            link = '<a href="/admin/submission/article/{pk}/change/">{pk}</a>'.format(pk=obj.article.pk)
            return mark_safe(link)
        else:
            return '-'


class FileHistoryAdmin(admin.ModelAdmin):
    """displays file history objects"""
    search_fields = ('original_filename', 'article_id')
    list_display = (
        'id', 'original_filename', 'article_id', 'mime_type', 'label',
        'history_seq',
    )
    list_filter = ('mime_type', 'article_id')
    raw_id_fields = ('owner',)


class XSLFileAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('date_uploaded', 'label', 'file')
    search_fields = ('label',)


class WorkflowElementAdmin(admin.ModelAdmin):
    search_fields = ('element_name',)
    list_display = ('element_name', 'journal', 'handshake_url', 'jump_url', 'stage', 'order')
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


class GalleyAdmin(admin.ModelAdmin):
    list_display = ('label', 'type', 'is_remote', 'article_pk', 'file_link')
    list_filter = ('type', 'is_remote', 'article')
    search_fields = ('label',)
    raw_id_fields = ('article', 'file', 'css_file')
    filter_horizontal = ('images',)

    def article_pk(self, obj):
        if obj.article:
            link = '<a href="/admin/submission/article/{pk}/change/">{pk}</a>'.format(pk=obj.article.pk)
            return mark_safe(link)
        else:
            return '-'

    def file_link(self, obj):
        if obj.file:
            link = '<a href="/admin/core/file/{pk}/change/">{pk}</a>'.format(pk=obj.file.pk)
            return mark_safe(link)
        else:
            return '-'


class EditorialGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'journal', 'sequence')
    list_filter = ('journal',)
    search_fields = ('name',)


class EditorialMemberAdmin(admin.ModelAdmin):
    list_display = ('pk', 'group', 'user', 'sequence')
    list_filter = ('group', 'user')
    raw_id_fields = ('group', 'user')


class ContactsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'object', 'sequence')
    search_fields = ('name', 'email', 'role')


class ContactAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'subject', 'client_ip', 'date_sent', 'object')
    list_filter = ('client_ip',)


class DomainAliasAdmin(admin.ModelAdmin):
    list_display = ('domain', 'redirect', 'journal')


class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('journal',)
    filter_horizontal = ('elements',)


class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'user_agent', 'timestamp')
    list_filter = ('ip_address',)


class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'journal', 'repository', 'role', 'requested', 'processed')
    list_filter = ('journal', 'repository', 'role', 'processed')


admin_list = [
    (models.AccountRole, AccountRoleAdmin),
    (models.Account, AccountAdmin),
    (models.Role, RoleAdmin,),
    (models.Setting, SettingAdmin),
    (models.SettingGroup, SettingGroupAdmin),
    (models.SettingValue, SettingValueAdmin),
    (models.File, FileAdmin),
    (models.FileHistory, FileHistoryAdmin),
    (models.XSLFile, XSLFileAdmin),
    (models.Interest,),
    (models.Task,),
    (models.TaskCompleteEvents,),
    (models.Galley, GalleyAdmin),
    (models.EditorialGroup, EditorialGroupAdmin),
    (models.EditorialGroupMember, EditorialMemberAdmin),
    (models.PasswordResetToken, PasswordResetAdmin),
    (models.OrcidToken, OrcidTokenAdmin),
    (models.DomainAlias, DomainAliasAdmin),
    (models.Country, CountryAdmin),
    (models.WorkflowElement, WorkflowElementAdmin),
    (models.HomepageElement, HomepageElementAdmin),
    (models.Workflow, WorkflowAdmin),
    (models.WorkflowLog, WorkflowLogAdmin),
    (models.LoginAttempt, LoginAttemptAdmin),
    (models.Contacts, ContactsAdmin),
    (models.Contact, ContactAdmin),
    (models.AccessRequest, AccessRequestAdmin),
]

[admin.site.register(*t) for t in admin_list]

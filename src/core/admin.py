__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.template.defaultfilters import truncatewords

from utils import admin_utils
from core import models, forms
from journal import models as journal_models
from repository import models as repository_models


class AccountRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'journal')
    list_filter = ('journal', 'role')
    search_fields = ('user__first_name', 'user__last_name',
                     'user__email', 'user__orcid',
                     'role__slug', 'role__name', 'journal__code')
    raw_id_fields = ('user',)


class SettingAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('pk', 'name', 'pretty_name', 'group',
                    'types', 'is_translatable')
    list_filter = ('group', 'types', 'is_translatable')
    search_fields = ('name', 'pretty_name', 'description')
    list_display_links = ('name', 'pretty_name',)

    inlines = [
        admin_utils.SettingValueInline
    ]


class AccountAdmin(UserAdmin):
    """Displays Account objects in the Django admin interface."""
    list_display = ('id', 'email', 'orcid', 'first_name', 'middle_name',
                    'last_name', 'institution', '_roles_in', 'last_login')
    list_display_links = ('id', 'email')
    list_filter = ('accountrole__journal',
                   'repositoryrole__repository__short_name',
                   'is_active', 'is_staff', 'is_admin', 'is_superuser',
                   'last_login')
    search_fields = ('id', 'username', 'email', 'first_name', 'middle_name',
                     'last_name', 'orcid', 'institution',
                     'biography', 'signature')

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': (
            'name_prefix', 'middle_name', 'orcid',
            'institution', 'department', 'country', 'twitter',
            'linkedin', 'facebook', 'github', 'website', 'biography', 'enable_public_profile',
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

    inlines = [
        admin_utils.AccountRoleInline,
        admin_utils.RepositoryRoleInline,
        admin_utils.EditorialGroupMemberInline,
        admin_utils.StaffGroupMemberInline,
        admin_utils.PasswordResetInline,
    ]

    def _roles_in(self, obj):
        if obj:
            journals = journal_models.Journal.objects.filter(
                accountrole__user=obj,
            ).distinct()
            repositories = repository_models.Repository.objects.filter(
                repositoryrole__user=obj,
            ).distinct()
            return ', '.join(
                [str(journal) for journal in journals] +
                [repository.short_name for repository in repositories]
            )
        else:
            return ''


class RoleAdmin(admin.ModelAdmin):
    """Displays Role objects in the Django admin interface."""
    list_display = ('slug', 'name')
    search_fields = ('slug', 'name',)


class PasswordResetAdmin(admin.ModelAdmin):
    """Displays Password Reset Data"""
    list_display = ('account', 'expiry', 'expired')
    search_fields = ('account__first_name', 'account__last_name',
                     'account__orcid', 'account__email')
    list_filter = ('expired', 'expiry')
    raw_id_fields = ('account',)
    date_hierarchy = ('expiry')


class SettingValueAdmin(admin.ModelAdmin):
    list_display = ('_setting_name', 'value', 'journal')
    list_filter = (
        'journal',
        'setting__types',
    )
    search_fields = (
        'setting__name',
        'setting__pretty_name',
        'setting__group__name',
        'setting__types',
        'value',
    )
    raw_id_fields = (
        'setting', 'journal',
    )

    @staticmethod
    def apply_select_related(self, qs):
        return qs.prefetch_related('journal', 'setting')

    def _setting_name(self, obj):
        return obj.setting.name if obj else ''


class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


class HomepageElementAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('name', 'active', 'object', 'sequence', 'configure_url',
                    'template_path', 'available_to_press', 'has_config')
    list_filter = (admin_utils.GenericRelationJournalFilter,
                   admin_utils.GenericRelationPressFilter,
                   'name', 'active', 'has_config', 'configure_url',
                   'template_path')
    search_fields = ('name',)


class FileAdmin(admin.ModelAdmin):
    """displays files"""
    list_display = ('id', 'original_filename', 'last_modified', 'label',
                    'owner', 'article_pk', '_journal')
    list_display_links = ('original_filename',)
    list_filter = (admin_utils.ArticleIDJournalFilter,
                   'last_modified', 'date_uploaded', 'mime_type',
                   'is_galley')
    search_fields = ('original_filename', 'article_id', 'label',
                     'description', 'owner__email', 'owner__first_name',
                     'owner__last_name')
    raw_id_fields = ('owner', 'history')
    readonly_fields = ['article_id']

    def article_pk(self, obj):
        if obj and obj.article_id:
            link = '<a href="/admin/submission/article/{pk}/change/">{pk}</a>'.format(pk=obj.article_id)
            return mark_safe(link)
        else:
            return '-'

    def _journal(self, obj):
        if obj and obj.article_id:
            return journal_models.Journal.objects.get(
                article__pk=obj.article_id
            ).code


class FileHistoryAdmin(admin.ModelAdmin):
    """displays file history objects"""
    list_display = ('id', 'original_filename', 'label',
                    'owner', 'history_seq', 'article_id')
    list_filter = ('mime_type',)
    search_fields = ('original_filename', 'article_id', 'label',
                     'description', 'owner__first_name',
                     'owner__last_name', 'owner__email')
    raw_id_fields = ('owner',)


class XSLFileAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('label', 'date_uploaded', 'file',
                    'original_filename', 'journal', '_comments')
    list_filter = ('journal', 'date_uploaded', 'label')
    search_fields = ('label', 'original_filename', 'comments')
    date_hierarchy = ('date_uploaded')

    def _comments(self, obj):
        return truncatewords(obj.comments, 10) if obj else ''


class SupplementaryFileAdmin(admin.ModelAdmin):
    list_display = ('label', 'file', '_date_uploaded', '_last_modified',
                    'doi', 'mime_type', '_journal')
    list_filter = (admin_utils.FileArticleIDJournalFilter,
                   'file__date_uploaded',
                   'file__last_modified',
                   'file__mime_type')
    search_fields = ('file__label', 'doi', 'file__original_filename')

    def _date_uploaded(self, obj):
        return obj.file.date_uploaded if obj else ''

    def _last_modified(self, obj):
        return obj.file.last_modified if obj else ''

    def _journal(self, obj):
        if obj and obj.file.article_id:
            return journal_models.Journal.objects.get(
                article__pk=obj.file.article_id
            ).code


class InterestAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', '_journals')
    list_display_links = ('pk', 'name',)
    list_filter = ('account__accountrole__journal',)
    search_fields = ('pk', 'name',)

    def _journals(self, obj):
        if obj and obj.account_set:
            journals = journal_models.Journal.objects.filter(
                accountrole__user__interest=obj,
            ).distinct()
            return ', '.join([journal.code for journal in journals])
        else:
            return ''

    inlines = [
        admin_utils.AccountInterestInline,
    ]


class TaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'object', 'completed_by',
                    'created', 'due', 'completed')
    list_display_links = ('pk', 'title',)
    list_filter = (admin_utils.GenericRelationArticleJournalFilter,
                   admin_utils.GenericRelationPreprintRepositoryFilter,
                   'title', 'created', 'due', 'completed')
    search_fields = ('pk', 'title', 'link', 'completed_by__first_name',
                     'completed_by__last_name', 'completed_by__email')


class TaskCompleteEventsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'event_name', )
    list_display_links = ('pk', 'event_name',)


class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('journal',)
    raw_id_fields = ('elements',)


class WorkflowElementAdmin(admin.ModelAdmin):
    list_display = ('element_name', 'journal', 'handshake_url',
                    'jump_url', 'stage', 'order')
    list_filter = ('journal', 'element_name', 'stage')
    search_fields = ('journal__code', 'element_name', 'stage')


class WorkflowLogAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', '_article', '_journal', '_workflow_element',
                    '_stage', 'timestamp')
    list_filter = ('element__journal', 'element__element_name',
                   'timestamp',)
    search_fields = ('article__title', 'element__element_name',
                     'element__stage', 'element__journal__code')
    date_hierarchy = ('timestamp')
    raw_id_fields = ('article',)

    def _stage(self, obj):
        return obj.element.stage if obj else ''

    def _workflow_element(self, obj):
        return obj.element.element_name if obj else ''


class OrcidTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'orcid', 'expiry')
    list_filter = ('expiry', )
    search_fields = ('orcid', )
    date_hierarchy = ('expiry')


class SettingGroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'enabled')
    list_filter = ('enabled',)
    search_fields = ('name',)
    list_display_links = ('name',)


class GalleyAdmin(admin.ModelAdmin):
    list_display = ('pk', 'label', 'last_modified', 'type',
                    'article_pk', 'file_link', 'file', '_journal')
    list_filter = (admin_utils.ArticleIDJournalFilter,
                   'last_modified', 'type', 'is_remote', 'public')
    search_fields = ('label', 'article__title', 'file__original_filename',
                     'article__id')
    raw_id_fields = ('article', 'file', 'css_file')
    filter_horizontal = ('images',)
    date_hierarchy = ('last_modified')

    def article_pk(self, obj):
        if obj and obj.article_id:
            link = '<a href="/admin/submission/article/{pk}/change/">{pk}</a>'.format(pk=obj.article_id)
            return mark_safe(link)
        else:
            return '-'

    def file_link(self, obj):
        if obj and obj.file:
            link = '<a href="/admin/core/file/{pk}/change/">{pk}</a>'.format(pk=obj.file.pk)
            return mark_safe(link)
        else:
            return '-'

    def _journal(self, obj):
        if obj and obj.article_id:
            return journal_models.Journal.objects.get(
                article__pk=obj.article_id
            ).code


class EditorialGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'journal', 'press', 'sequence')
    list_filter = ('journal', 'press')
    search_fields = ('name',)

    inlines = [
        admin_utils.EditorialGroupMemberInline
    ]


class EditorialMemberAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'group', '_journal', 'sequence')
    list_filter = ('group__journal', 'group')
    raw_id_fields = ('user', )
    search_fields = ('pk', 'user__first_name', 'user__last_name',
                     'user__email', 'group__name', 'group__description')

    def _journal(self, obj):
        return obj.group.journal if obj else ''


class ContactsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'object', 'sequence')
    list_filter = (admin_utils.GenericRelationJournalFilter,
                   admin_utils.GenericRelationPressFilter)
    search_fields = ('name', 'email', 'role')


class ContactAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient',
                    'client_ip', 'date_sent', 'object')
    list_filter = (admin_utils.GenericRelationJournalFilter,
                   admin_utils.GenericRelationPressFilter,
                   'date_sent', 'recipient')
    search_fields = ('subject', 'sender', 'recipient',)
    date_hierarchy = ('date_sent')


class DomainAliasAdmin(admin.ModelAdmin):
    list_display = ('domain', 'redirect', 'site_object', 'redirect_url')
    list_filter = ('journal', 'press')
    search_fields = ('domain',)


class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'user_agent', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('ip_address', 'user_agent',)
    date_hierarchy = ('timestamp')


class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'journal', 'repository', 'role',
                    'requested', 'processed')
    list_filter = ('journal', 'repository', 'role', 'processed')
    search_fields = ('user__first_name', 'user__last_name', 'user__email',
                     'journal__code', 'repository__short_name', 'role__slug',
                     'role__name')
    raw_id_fields = ('user',)
    date_hierarchy = ('requested')


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
    (models.SupplementaryFile, SupplementaryFileAdmin),
    (models.Interest, InterestAdmin),
    (models.Task, TaskAdmin),
    (models.TaskCompleteEvents, TaskCompleteEventsAdmin),
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

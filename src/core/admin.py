__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from core import models, forms


class PasswordResetInline(admin.TabularInline):
    model = models.PasswordResetToken
    extra = 0


class AccountRoleInline(admin.TabularInline):
    model = models.AccountRole
    extra = 0


class SettingInline(admin.TabularInline):
    model = models.Setting
    extra = 0


class SettingValueInline(admin.TabularInline):
    model = models.SettingValue
    extra = 0
    fields = ('journal', 'value')


class FileInline(admin.TabularInline):
    model = models.File
    extra = 0
    fields = ('journal', 'value')


class TaskCompleteEventInline(admin.TabularInline):
    model = models.Task.complete_events.through
    extra = 0


class EditorialGroupMemberInline(admin.TabularInline):
    model = models.EditorialGroupMember
    extra = 0


class WorkflowLogInline(admin.TabularInline):
    model = models.WorkflowLog
    extra = 0
    raw_id_fields = ('article',)


class AccountRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'journal')
    list_filter = ('role', 'journal')
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
        SettingValueInline
    ]


class AccountAdmin(UserAdmin):
    """Displays Account objects in the Django admin interface."""
    list_display = ('email', 'orcid', 'first_name', 'middle_name',
                    'last_name', 'institution', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_admin', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'middle_name',
                     'last_name', 'orcid', 'institution',
                     'biography', 'signature')
    date_hierarchy = ('last_login')

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

    inlines = [
        PasswordResetInline,
        AccountRoleInline,
        EditorialGroupMemberInline,
    ]


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
    list_display = ('setting_pretty_name', 'journal', 'value')
    list_filter = ('journal', )
    search_fields = ('journal__code', 'setting__name',
                     'setting__pretty_name', 'setting__group__name')
    raw_id_fields = (
        'setting', 'journal',
    )

    @staticmethod
    def apply_select_related(self, qs):
        return qs.prefetch_related('journal', 'setting')

    def setting_pretty_name(self, obj):
        return obj.setting.pretty_name


class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


class HomepageElementAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('name', 'active', 'object', 'sequence', 'configure_url',
                    'template_path', 'available_to_press', 'has_config')
    list_filter = ('name', 'active', 'has_config', 'configure_url',
                   'template_path')
    search_fields = ('name', 'object__code')


class FileAdmin(admin.ModelAdmin):
    """displays files"""
    list_display = ('id', 'original_filename', 'label',
                    'self_article_path', 'owner', 'article_pk')
    list_display_links = ('original_filename',)
    list_filter = ('last_modified', 'date_uploaded', 'mime_type',
                   'label', 'is_galley')
    search_fields = ('original_filename', 'article_id', 'label',
                     'description')
    raw_id_fields = ('owner',)
    filter_horizontal = ('history',)
    readonly_fields = ['article_id']
    date_hierarchy = ('last_modified')

    def article_pk(self, obj):
        if obj.article:
            link = '<a href="/admin/submission/article/{pk}/change/">{pk}</a>'.format(pk=obj.article.pk)
            return mark_safe(link)
        else:
            return '-'


class FileHistoryAdmin(admin.ModelAdmin):
    """displays file history objects"""
    list_display = ('id', 'original_filename', 'label',
                    'owner', 'history_seq', 'article_id')
    list_filter = ('mime_type', 'label')
    search_fields = ('original_filename', 'article_id', 'label',
                     'description', 'owner__first_name',
                     'owner__last_name', 'owner__email')
    raw_id_fields = ('owner',)


class XSLFileAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('label', 'date_uploaded', 'file',
                    'original_filename')
    list_filter = ('date_uploaded', 'label')
    search_fields = ('label', 'original_filename', 'comments')
    date_hierarchy = ('date_uploaded')


class SupplementaryFileAdmin(admin.ModelAdmin):
    list_display = ('label', 'file', 'date_uploaded', 'last_modified',
                    'doi', 'path', 'mime_type')
    search_fields = ('file__label', 'doi', 'file__original_filename')


class InterestAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name',)
    list_display_links = ('pk', 'name',)
    search_fields = ('pk', 'name',)


class TaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'object', 'link', 'completed_by',
                    'created', 'due', 'completed')
    list_display_links = ('pk', 'title',)
    list_filter = ('title', 'created', 'due', 'completed')
    search_fields = ('pk', 'title', 'link', 'completed_by__first_name',
                     'completed_by__last_name', 'completed_by__email')
    date_hierarchy = ('created')


class TaskCompleteEventsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'event_name', )
    list_display_links = ('pk', 'event_name',)

    inlines = [
        TaskCompleteEventInline
    ]


class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('journal',)
    filter_horizontal = ('elements',)


class WorkflowElementAdmin(admin.ModelAdmin):
    list_display = ('element_name', 'journal', 'handshake_url',
                    'jump_url', 'stage', 'order')
    list_filter = ('journal', 'element_name', 'stage')
    search_fields = ('journal__code', 'element_name', 'stage')

    inlines = [
        WorkflowLogInline
    ]


class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'article', 'element', 'stage', 'timestamp')
    list_filter = ('element', )
    search_fields = ('article__title', 'element__element_name',
                     'element__stage', 'element__journal__code')
    date_hierarchy = ('timestamp')

    def stage(self, obj):
        if obj:
            return obj.element.stage
        else:
            return ''


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

    inlines = [
        SettingInline
    ]


class GalleyAdmin(admin.ModelAdmin):
    list_display = ('pk', 'label', 'type',
                    'article_pk', 'file_link', 'file')
    list_display_links = ('label',)
    list_filter = ('type', 'is_remote', 'public')
    search_fields = ('label', 'article__title', 'file__original_filename',
                     'article__id')
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

    def original_filename(self, obj):
        if obj.file:
            return obj.file.original_filename
        else:
            return '-'


class EditorialGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'journal', 'sequence')
    list_filter = ('journal',)
    search_fields = ('name', 'journal__code')

    inlines = [
        EditorialGroupMemberInline
    ]


class EditorialMemberAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'group', 'sequence')
    list_filter = ('group', )
    raw_id_fields = ('user', )
    search_fields = ('pk', 'user__first_name', 'user__last_name',
                     'user__email', 'group__name', 'group__description',
                     'group__journal__code')


class ContactsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'object', 'sequence')
    search_fields = ('name', 'email', 'role')


class ContactAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient',
                    'client_ip', 'date_sent', 'object')
    list_filter = ('date_sent', 'recipient')
    search_fields = ('subject', 'sender', 'recipient',)
    date_hierarchy = ('date_sent')


class DomainAliasAdmin(admin.ModelAdmin):
    list_display = ('domain', 'redirect', 'site_object', 'redirect_url')
    search_fields = ('domain', 'journal__code', 'press__name')


class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'user_agent', 'timestamp')
    list_filter = ('ip_address', 'timestamp')
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

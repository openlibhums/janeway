__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from hvad.admin import TranslatableAdmin

from core import models


class SettingAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('name', 'group', 'types')
    list_filter = ('group', 'types')


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


class SettingValueAdmin(TranslatableAdmin):
    pass


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
    search_fields = ('original_filename', 'uuid_filename')
    list_display = ('id', 'original_filename', 'uuid_filename', 'mime_type', 'article')
    list_filter = ('mime_type',)


class WorkflowElementAdmin(admin.ModelAdmin):
    search_fields = ('element_name',)
    list_display = ('element_name', 'journal', 'handshake_url', 'stage', 'order')
    list_filter = ('journal',)
    

class WorkflowLogAdmin(admin.ModelAdmin):
    search_fields = ('article',)
    list_display = ('article', 'element', 'timestamp')
    list_filter = ('element',)


admin_list = [
    (models.Account, AccountAdmin),
    (models.Role, RoleAdmin,),
    (models.Setting, SettingAdmin),
    (models.SettingGroup,),
    (models.SettingValue, SettingValueAdmin),
    (models.File, FileAdmin),
    (models.AccountRole,),
    (models.Interest,),
    (models.Task,),
    (models.TaskCompleteEvents,),
    (models.Galley,),
    (models.EditorialGroup,),
    (models.EditorialGroupMember,),
    (models.PasswordResetToken, PasswordResetAdmin),
    (models.OrcidToken,),
    (models.DomainAlias,),
    (models.Country, CountryAdmin),
    (models.WorkflowElement, WorkflowElementAdmin),
    (models.HomepageElement, HomepageElementAdmin),
    (models.WorkflowLog, WorkflowLogAdmin),
    (models.LoginAttempt,),
]

[admin.site.register(*t) for t in admin_list]

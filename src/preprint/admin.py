__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from preprint import models


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled')
    list_filter = ('enabled',)
    search_fields = ('name', 'slug')
    filter_horizontal = ('editors', 'preprints')


admin_list = [
    (models.PreprintVersion,),
    (models.Comment,),
    (models.Subject, SubjectAdmin),
    (models.VersionQueue,),
]

[admin.site.register(*t) for t in admin_list]

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from production import models


class ProductionAssignmentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'production_manager', 'editor', 'assigned', 'closed', 'accepted_by_manager')
    list_filter = ('article', 'production_manager', 'editor')
    raw_id_fields = ('article', 'production_manager', 'editor', 'accepted_by_manager')


class TypesetTaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'assignment', 'typesetter', 'assigned', 'notified', 'accepted', 'completed', 'editor_reviewed')
    list_filter = ('assignment', 'typesetter', 'notified', 'editor_reviewed')
    raw_id_fields = ('assignment', 'typesetter')
    filter_horizontal = ('files_for_typesetting', 'galleys_loaded')


admin_list = [
    (models.ProductionAssignment, ProductionAssignmentAdmin),
    (models.TypesetTask, TypesetTaskAdmin),
]

[admin.site.register(*t) for t in admin_list]

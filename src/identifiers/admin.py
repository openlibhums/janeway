__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from identifiers import models


class DOIAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'resolves_to', 'expected_to_resolve_to', 'checked')
    raw_id_fields = ('article', 'identifier')


class Identifier(admin.ModelAdmin):
    list_display = ('pk', 'id_type', 'identifier', 'enabled', 'article')
    raw_id_fields = ('article',)


admin_list = [
    (models.Identifier, Identifier),
    (models.BrokenDOI, DOIAdmin),
]

[admin.site.register(*t) for t in admin_list]

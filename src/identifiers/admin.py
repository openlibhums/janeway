__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from identifiers import models


class DOIAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('identifier', 'resolves_to', 'expected_to_resolve_to', 'checked')


admin_list = [
    (models.Identifier,),
    (models.BrokenDOI, DOIAdmin),
]

[admin.site.register(*t) for t in admin_list]

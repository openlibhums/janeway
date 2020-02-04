__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from plugins.typesetting import models


class TypesettingRoundAdmin(admin.ModelAdmin):
    list_display = ('article', 'round_number', 'date_created')
    list_filter = ('article', 'round_number',)
    raw_id_fields = ('article',)


admin_list = [
    (models.TypesettingRound, TypesettingRoundAdmin),
    (models.TypesettingClaim, ),
]

[admin.site.register(*t) for t in admin_list]
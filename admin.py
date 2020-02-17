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


class TypesettingAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'article_title',
        'round',
        'typesetter',
        'friendly_status',
        'pk',
    )
    raw_id_fields = (
        'typesetter',
        'manager',
        'round',
    )
    filter_horizontal = (
        'files_to_typeset',
        'galleys_created',
    )

    def article_title(self, obj):
        return obj.round.article.title


admin_list = [
    (models.TypesettingRound, TypesettingRoundAdmin),
    (models.TypesettingClaim, ),
    (models.TypesettingAssignment, TypesettingAssignmentAdmin),
]

[admin.site.register(*t) for t in admin_list]
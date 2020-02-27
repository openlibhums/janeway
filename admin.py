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
        'manager',
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
    search_fields = (
        'typesetter',
        'manager',
    )

    @staticmethod
    def article_title(obj):
        return obj.round.article.title


class GalleyProofingAdmin(admin.ModelAdmin):
    list_display = (
        'article_title',
        'round',
        'proofreader',
        'manager',
        'pk',
    )
    raw_id_fields = (
        'proofreader',
        'manager',
        'round'
    )
    filter_horizontal = (
        'annotated_files',
    )
    search_fields = (
        'proofreader',
        'manager',
    )

    @staticmethod
    def article_title(obj):
        return obj.round.article.title


admin_list = [
    (models.TypesettingRound, TypesettingRoundAdmin),
    (models.TypesettingClaim, ),
    (models.TypesettingAssignment, TypesettingAssignmentAdmin),
    (models.GalleyProofing, GalleyProofingAdmin),
]

[admin.site.register(*t) for t in admin_list]
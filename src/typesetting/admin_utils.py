__copyright__ = "Copyright 2022 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers, Mauro Sanchez and Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck, University of London"

from django.contrib import admin
from typesetting import models as typesetting_models


class TypesettingClaimInline(admin.TabularInline):
    model = typesetting_models.TypesettingClaim
    extra = 0
    raw_id_fields = ('article', 'editor')


class TypesettingAssignmentInline(admin.TabularInline):
    model = typesetting_models.TypesettingAssignment
    extra = 0
    fields = ('round', 'manager', 'typesetter', 'assigned', 'due', 'task')
    raw_id_fields = ('round', 'manager', 'typesetter')


class TypesettingCorrectionInline(admin.TabularInline):
    model = typesetting_models.TypesettingCorrection
    extra = 0
    raw_id_fields = ('task', 'galley')


class GalleyProofingInline(admin.TabularInline):
    model = typesetting_models.GalleyProofing
    extra = 0
    fields = ('round', 'manager', 'proofreader', 'assigned', 'due', 'task')
    raw_id_fields = ('round', 'manager', 'proofreader')

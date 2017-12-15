__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.contrib import admin
from review import models

admin_list = [
    (models.EditorAssignment,),
    (models.ReviewAssignment,),
    (models.ReviewForm,),
    (models.ReviewFormElement,),
    (models.ReviewAssignmentAnswer,),
    (models.ReviewRound,),
    (models.ReviewerRating,),
    (models.RevisionAction,),
    (models.RevisionRequest,),
    (models.EditorOverride,),
    (models.DecisionDraft,),
]

[admin.site.register(*t) for t in admin_list]

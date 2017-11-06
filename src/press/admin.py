__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from press import models


class PressAdmin(SummernoteModelAdmin):
    list_display = ('name', 'domain', 'theme', 'is_secure')


admin_list = [
    (models.Press, PressAdmin),
    (models.PressSetting,)
]

[admin.site.register(*t) for t in admin_list]

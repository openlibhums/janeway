__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django import forms
from django.utils.translation import gettext_lazy as _

from core import forms as core_forms


class ArchiveArticleForm(core_forms.ConfirmableForm):
    CONFIRMABLE_BUTTON_NAME = 'archive'
    CONFIRMED_BUTTON_NAME = 'confirm'
    QUESTION = _('Are you sure you want to archive this article?')

    def check_for_potential_errors(self):
        # This customizes the confirmable form method
        potential_errors = ["asd"]

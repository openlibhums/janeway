from django.db.models.signals import post_save

from journal import models as journal_models
from submission import models as submission_models
from core import models as core_models

from utils import setting_handler
from utils.upgrade import shared


SETTINGS_TO_CHANGE = [
    {'group': 'email', 'name': 'copyeditor_assignment_notification', 'action': 'update'},
]

def update_settings():
    for journal in journal_models.Journal.objects.all():
        setting_handler.update_settings(SETTINGS_TO_CHANGE, journal)

def execute():
    shared.check_version(script='1.3.2')
    update_settings()
    shared.set_version('1.3.2')

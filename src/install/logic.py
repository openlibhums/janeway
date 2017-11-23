__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from utils import setting_handler


def get_initial_settings(journal, settings_to_get):
    settings = {}
    for setting in settings_to_get:
        got = setting_handler.get_setting('general', setting, journal).value
        settings[setting] = got

    return settings

__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import glob

from django.conf import settings

from cms import models as models
from utils import setting_handler


def get_custom_templates_folder(journal):
    setting = setting_handler.get_setting(
        'general',
        'custom_cms_templates',
        journal,
        default=False,
    )
    return setting.processed_value if setting else ''


def get_custom_templates_path(journal, press):
    if journal:
        theme = setting_handler.get_setting(
            'general',
            'journal_theme',
            journal,
        ).processed_value
    elif press and press.theme:
        theme = press.theme
    else:
        return ''

    folder = get_custom_templates_folder(journal)
    if not folder:
        return ''

    return os.path.join(settings.BASE_DIR, 'themes', theme, 'templates', folder)


def get_custom_templates(journal, press):

    templates_folder = get_custom_templates_folder(journal)
    templates_path = get_custom_templates_path(journal, press)
    if not templates_folder or not templates_path:
        return []

    custom_templates = [('','-----')]
    for filepath in sorted(glob.glob(os.path.join(templates_path, '*.html'))):
        choice = (
            os.path.join(templates_folder, os.path.basename(filepath)),
            os.path.basename(filepath),
        )
        custom_templates.append(choice)
    return custom_templates

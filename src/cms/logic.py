__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import glob

from django.conf import settings

from cms import models as models
from utils import setting_handler

def get_custom_templates(journal, press):

    if journal:
        theme = setting_handler.get_setting(
            'general',
            'journal_theme',
            journal,
        ).processed_value
    elif press and press.theme:
        theme = press.theme
    else:
        theme = None

    if not theme:
        return []

    custom_templates_setting = setting_handler.get_setting(
        'general',
        'custom_cms_templates',
        journal,
        default=False,
    )
    if not custom_templates_setting:
        return []

    custom_templates_folder = custom_templates_setting.processed_value
    custom_templates_path = os.path.join(
        settings.BASE_DIR,
        'themes',
        theme,
        'templates',
        custom_templates_folder,
        '*.html'
    )
    custom_templates = [('','-----')]
    for filepath in sorted(glob.glob(custom_templates_path)):
        choice = (
            os.path.join(
                custom_templates_folder,
                os.path.basename(filepath)
            ),
            os.path.basename(filepath),
        )
        custom_templates.append(choice)

    return custom_templates

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import random

from journal import models as journal_models
from core.homepage_elements.journals_and_html import plugin_settings
from utils.logger import get_logger
from press import models as press_models

logger = get_logger(__name__)


def get_random_journals():
    journals = journal_models.Journal.objects.filter(
        hide_from_press=False,
    )

    sample_size = 6 if journals.count() > 6 else journals.count()

    return random.sample(set(journals), sample_size)


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(
            name=plugin_settings.PLUGIN_NAME,
    ).exists():

        if request.press.random_featured_journals:
            featured_journals = get_random_journals()
        else:
            featured_journals = request.press.featured_journals.all()

        setting, c = press_models.PressSetting.objects.get_or_create(
            press=request.press,
            name='journals_and_html_content',
        )
        html_block_content = setting.value

        if not setting.value:
            html_block_content = '<p>This element has no content.</p>'

        return {
            'featured_journals': featured_journals,
            'html_block_content': html_block_content,
        }
    else:
        return {}

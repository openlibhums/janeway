__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import random

from journal import models as journal_models
from utils.function_cache import cache


def get_random_journals():
    journals = journal_models.Journal.objects.filter(
        hide_from_press=False,
    )

    sample_size = min(6, journals.count())

    return random.sample(set(journals), sample_size)


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(name='Journals').exists():

        if request.press.random_featured_journals:
            featured_journals = get_random_journals()
        else:
            featured_journals = request.press.featured_journals.all()

        return {'featured_journals': sorted(featured_journals, key=lambda x: x.name)}
    else:
        return {}

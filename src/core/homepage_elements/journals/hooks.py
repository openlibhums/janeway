__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import random

from journal import models as journal_models
from utils.function_cache import cache


@cache(120)
def get_random_journals():
    journals = journal_models.Journal.objects.filter(hide_from_press=False)
    journal_pks = [journal.pk for journal in journals]
    random_journal_pks = list()

    random.shuffle(journal_pks)
    for i in range(0, 6):
        choice = journal_pks.pop()
        random_journal_pks.append(choice)

    return journals.filter(pk__in=random_journal_pks)\


def yield_homepage_element_context(request, homepage_elements):
    print('hook')
    if homepage_elements is not None and homepage_elements.filter(name='Journals').exists():

        if request.press.random_featured_journals:
            featured_journals = get_random_journals()
        else:
            featured_journals = request.press.featured_journals.all()

        print(featured_journals, 'sdfsd')

        return {'featured_journals': featured_journals}
    else:
        return {}

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import random

from django.utils import timezone

from submission import models as submission_models


def get_random_preprints():
    preprints = submission_models.Article.preprints.filter(stage=submission_models.STAGE_PREPRINT_PUBLISHED,
                                                           date_published__lte=timezone.now())
    preprint_pks = [preprint.pk for preprint in preprints]
    random_preprints = list()
    random.shuffle(preprint_pks)

    for i in range(0, 3):
        if preprint_pks:
            choice = preprint_pks.pop()
            random_preprints.append(choice)

    return preprints.filter(pk__in=random_preprints)


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(name='Preprints').exists():
        if request.press.random_homepage_preprints:
            return {'preprints': get_random_preprints()}
        else:
            print(request.press.homepage_preprints.all())
            return {'preprints': request.press.homepage_preprints.all()}
    else:
        return {}

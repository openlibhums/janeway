__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "The Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "The Open Library of Humanities"

from cms import models as cms_models

from django.contrib.contenttypes.models import ContentType


def get_navigation_items(press):
    content_type = ContentType.objects.get_for_model(press)
    return cms_models.NavigationItem.objects.filter(
        content_type=content_type,
        object_id=press.pk,
        top_level_nav__isnull=True,
    ).order_by('sequence')

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.apps import AppConfig
from django.db import models


class CoreConfig(AppConfig):
    """Configures the core app."""

    name = "core"

    def ready(self):
        from core import upgrade  # register upgrade signals
        from core.model_utils import SearchLookup
        from utils.language import get_constrained_language
        from django.utils import translation as django_translation

        models.CharField.register_lookup(SearchLookup)
        models.TextField.register_lookup(SearchLookup)

        # Override Django's get_language with our constrained version
        django_translation.get_language = get_constrained_language

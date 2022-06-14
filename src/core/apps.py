__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.apps import AppConfig
from django.db import models


class CoreConfig(AppConfig):
    """Configures the core app."""
    name = 'core'

    def ready(self):
        from core.model_utils import SearchLookup
        models.CharField.register_lookup(SearchLookup)
        models.TextField.register_lookup(SearchLookup)

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys

from utils import load_janeway_settings

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("JANEWAY_SETTINGS_MODULE", "core.settings")

load_janeway_settings()

application = get_wsgi_application()

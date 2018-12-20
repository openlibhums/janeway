__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import importlib
import logging
import os
import threading

from django.conf import settings

from core import janeway_global_settings

LOCK = threading.Lock()

def load_janeway_settings():

    with LOCK:
        if settings.configured:
            return

        settings_module = os.environ["JANEWAY_SETTINGS_MODULE"]
        janeway_settings = {
            k: v for k, v in janeway_global_settings.__dict__.items()
            if k.isupper()
        }
        if os.environ["JANEWAY_SETTINGS_MODULE"] != "core.janeway_global_settings":
            custom_module = importlib.import_module(os.environ["JANEWAY_SETTINGS_MODULE"])
            custom_settings = {
                k: v for k, v in custom_module.__dict__.items()
                if k.isupper()
            }
            logging.debug(
                "Loading settings from %s: %s" % (
                    os.environ["JANEWAY_SETTINGS_MODULE"],
                    custom_settings.keys(),
            ))
            janeway_settings = dict(janeway_settings, **custom_settings)

        settings.configure(**janeway_settings)

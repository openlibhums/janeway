__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import importlib
import itertools
from functools import singledispatch
import logging
import os
import threading

from django.conf import settings

from core import janeway_global_settings

LOCK = threading.Lock()

MERGEABLE_SETTINGS = {"INSTALLED_APPS", "MIDDLEWARE_CLASSES"}

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
            logging.info(
                "Loading settings from %s" % (
                    os.environ["JANEWAY_SETTINGS_MODULE"],
            ))
            logging.debug(
                    "Loading the following custom settings: %s" %(
                    custom_settings.keys(),
            ))
            for k, v in custom_settings.items():
                if k in MERGEABLE_SETTINGS:
                    janeway_settings[k] = merge_settings(janeway_settings[k], v)
                else:
                    janeway_settings[k] = v

        settings.configure(**janeway_settings)

@singledispatch
def merge_settings(base, override):
    return override

@merge_settings.register(list)
@merge_settings.register(tuple)
@merge_settings.register(set)
def merge_iterable_settings(base, override):
    factory = type(base)
    return factory(itertools.chain(base, override))

@merge_settings.register(dict)
def merge_dict_settings(base, override):
    merged = {}

    for k, v in override.items():
        if k in base:
            merged[k] = merge_settings(base[k], v)
        else:
            merged[k] = v

    return dict(base, **merged)

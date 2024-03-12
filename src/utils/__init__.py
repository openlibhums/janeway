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

import django
from django.conf import settings
from django.test.utils import get_runner

from core import janeway_global_settings

LOCK = threading.Lock()

MERGEABLE_SETTINGS = {"INSTALLED_APPS", "MIDDLEWARE"}

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
            mergeable_settings = custom_settings.get(
                "MERGEABLE_SETTINGS", MERGEABLE_SETTINGS,
            )
            for k, v in custom_settings.items():
                if k in mergeable_settings:
                    janeway_settings[k] = merge_settings(janeway_settings[k], v)
                else:
                    janeway_settings[k] = v

        settings.configure(**janeway_settings)
        django.setup()

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


def janeway_test_runner_wrapper(*args, **kwargs):
    """ A test runner wrapper that will initialise the test database

    The original test runner will still be returned, but ensuring the required
    state exists in the database before the test runs
    """

    if not getattr(settings, 'CHOSEN_TEST_RUNNER', None):
        settings.CHOSEN_TEST_RUNNER = 'django.test.runner.DiscoverRunner'
    from utils import install
    install.update_settings(management_command=False)
    install.update_emails(management_command=False)
    install.update_xsl_files(management_command=False)
    settings.TEST_RUNNER = settings.CHOSEN_TEST_RUNNER
    TestRunner =  get_runner(settings)
    return TestRunner(*args, **kwargs)

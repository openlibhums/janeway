__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf import settings

import os


def load_plugin_apps():
    path = os.path.join(settings.BASE_DIR, "plugins")
    root, dirs, files = next(os.walk(path))

    return ['plugins.{0}'.format(dir) for dir in dirs if dir != '__pycache__']


def load_plugin_templates():
    path = os.path.join(settings.BASE_DIR, "plugins")
    root, dirs, files = next(os.walk(path))

    return ['{0}/plugins/{1}/templates/'.format(settings.BASE_DIR, dir) for dir in dirs if dir != '__pycache__']


def load_homepage_element_apps():
    path = os.path.join(settings.BASE_DIR, "core", "homepage_elements")
    root, dirs, files = next(os.walk(path))

    return ['core.homepage_elements.{0}'.format(dir) for dir in dirs if dir != '__pycache__']


def load_homepage_element_templates():
    path = os.path.join(settings.BASE_DIR, "core", "homepage_elements")
    root, dirs, files = next(os.walk(path))

    return ['{0}/core/homepage_elements/{1}/templates/'.format(
        settings.BASE_DIR, dir) for dir in dirs if dir != '__pycache__']


def load_plugin_locales():
    path = os.path.join(settings.BASE_DIR, "plugins")
    root, dirs, files = next(os.walk(path))
    return [os.path.join(settings.BASE_DIR, 'plugins', dir, 'locales') for dir in dirs if dir != '__pycache__']

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os


def load_plugin_apps(base_dir):
    path = os.path.join(base_dir, "plugins")
    root, dirs, files = next(os.walk(path))

    return ['plugins.{0}'.format(dir) for dir in dirs if dir != '__pycache__']


def load_plugin_templates(base_dir):
    path = os.path.join(base_dir, "plugins")
    root, dirs, files = next(os.walk(path))

    return ['{0}/plugins/{1}/templates/'.format(base_dir, dir) for dir in dirs if dir != '__pycache__']


def load_homepage_element_apps(base_dir):
    path = os.path.join(base_dir, "core", "homepage_elements")
    root, dirs, files = next(os.walk(path))

    return ['core.homepage_elements.{0}'.format(dir) for dir in dirs if dir != '__pycache__']


def load_homepage_element_templates(base_dir):
    path = os.path.join(base_dir, "core", "homepage_elements")
    root, dirs, files = next(os.walk(path))

    return ['{0}/core/homepage_elements/{1}/templates/'.format(
        base_dir, dir) for dir in dirs if dir != '__pycache__']


def load_plugin_locales(base_dir):
    path = os.path.join(base_dir, "plugins")
    root, dirs, files = next(os.walk(path))
    return [os.path.join(base_dir, 'plugins', dir, 'locales') for dir in dirs if dir != '__pycache__']

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf import settings
from django.db.utils import ProgrammingError

from utils import models

import os
from importlib import import_module


def get_dirs(directory):
    path = os.path.join(settings.BASE_DIR, directory)
    root, dirs, files = next(os.walk(path))

    dirs = [x for x in dirs if x != '__pycache__']

    return dirs


def load(directory="plugins", prefix="plugins", permissive=False):
    # Get all of the folders in the plugins folder, check if they are installed and then
    # load up their hooks.
    dirs = get_dirs(directory)

    hooks = []
    plugins = []
    for dir in dirs:
        plugin = get_plugin(dir, permissive)
        if plugin:
            plugins.append(plugin)
            module_name = "{0}.{1}.plugin_settings".format(prefix, dir)

            # Load hooks
            hooks.append(load_hooks(module_name))

            # Check for workflow
            workflow_check = check_plugin_workflow(module_name)
            if workflow_check:
                settings.WORKFLOW_PLUGINS[workflow_check] = module_name

            # Call event registry
            register_for_events(module_name)

    # Register plugin hooks
    if settings.PLUGIN_HOOKS:
        super_hooks = settings.PLUGIN_HOOKS
    else:
        settings.PLUGIN_HOOKS = {}
        super_hooks = {}

    for _dict in hooks:
        if _dict:
            for k, v in _dict.items():
                super_hooks.setdefault(k, []).append(v)

    for k, v in super_hooks.items():
        settings.PLUGIN_HOOKS[k] = v

    return plugins


def get_plugin(module_name, permissive):
    # Check that the module is installed.
    if permissive:
        plugin = models.Plugin()
        plugin.name = module_name
        plugin.enabled = True

        return plugin
    try:
        plugin = models.Plugin.objects.get(name=module_name, enabled=True)
        return plugin
    except (models.Plugin.DoesNotExist, ProgrammingError):
        return False


def load_hooks(module_name):
    plugin_settings = import_module(module_name)
    return plugin_settings.hook_registry()


def check_plugin_workflow(module_name):
    plugin_settings = import_module(module_name)
    try:
        if plugin_settings.IS_WORKFLOW_PLUGIN:
            return plugin_settings.PLUGIN_NAME
    except AttributeError:
        return False


def register_for_events(module_name):
    plugin_settings = import_module(module_name)

    try:
        plugin_settings.register_for_events()
    except AttributeError:
        # Pass, this module has no register_for_events func
        pass

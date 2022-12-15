__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os
from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError, ProgrammingError

from core.workflow import ELEMENT_STAGES, STAGES_ELEMENTS
from submission.models import PLUGIN_WORKFLOW_STAGES
from utils import models
from utils.logic import get_janeway_version


def get_dirs(directory):
    path = os.path.join(settings.BASE_DIR, directory)
    root, dirs, files = next(os.walk(path))

    dirs = [x for x in dirs if x != '__pycache__']

    return dirs


def register_hooks(hooks: list):
    """Register plugin hooks."""
    # Hooks are dictionaries. For a description,
    # see "Technical Configuration" (docs/source/configuration.rst)
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


def load(directory="plugins", prefix="plugins", permissive=False):
    # Get all of the folders in the plugins folder, check if they are
    # installed and then load up their hooks.
    dirs = get_dirs(directory)

    hooks = []
    plugins = []
    for dir in dirs:
        plugin = get_plugin(dir, permissive)
        if plugin:
            plugins.append(plugin)
            module_name = "{0}.{1}.plugin_settings".format(prefix, dir)

            # Load settings module
            plugin_settings = import_module(module_name)
            validate_plugin_version(plugin_settings)

            # Load hooks
            hooks.append(load_hooks(plugin_settings))

            # Check for workflow
            workflow_check = check_plugin_workflow(plugin_settings)
            if workflow_check:
                settings.WORKFLOW_PLUGINS[workflow_check] = module_name
                PLUGIN_WORKFLOW_STAGES.append(
                    (plugin_settings.STAGE, plugin_settings.PLUGIN_NAME)
                )
                ELEMENT_STAGES[
                    plugin_settings.PLUGIN_NAME] = [plugin_settings.STAGE]

                STAGES_ELEMENTS[
                    plugin_settings.STAGE] = plugin_settings.PLUGIN_NAME

            # Call event registry
            register_for_events(plugin_settings)

    register_hooks(hooks)
    return plugins


def validate_plugin_version(plugin_settings):
    valid = None
    try:
        wants_version = plugin_settings.JANEWAY_VERSION.split(".")
    except AttributeError:
        # No MIN version pinned by plugin
        return

    current_version = get_janeway_version().split(".")

    for current, wants in zip(current_version, wants_version):
        current, wants = int(current), int(wants)
        if current > wants:
            valid = True
            break
        elif current < wants:
            valid = False
            break

    if valid is None:  # Handle exact match
        valid = True

    if not valid:
        raise ImproperlyConfigured(
            "Plugin {} not  compatibile with current install: {} < {}".format(
                plugin_settings.PLUGIN_NAME, current_version, wants_version
            )
        )


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
    except (
            models.Plugin.DoesNotExist,
            models.Plugin.MultipleObjectsReturned,
            ProgrammingError,
            OperationalError,
        ) as e:
        if settings.DEBUG:
            print('Error loading plugin {0} {1}'.format(module_name, e))
        return False


def load_hooks(plugin_settings):
    return plugin_settings.hook_registry()


def check_plugin_workflow(plugin_settings):
    try:
        if plugin_settings.IS_WORKFLOW_PLUGIN:
            return plugin_settings.PLUGIN_NAME
    except AttributeError:
        return False


def register_for_events(plugin_settings):
    try:
        plugin_settings.register_for_events()
    except AttributeError:
        # Pass, this module has no register_for_events func
        pass

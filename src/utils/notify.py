__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import os
from django.conf import settings


def notification(**kwargs):

    # kwargs should include:
    # action: a list of frameworks to use or "all". NB Email cannot be sent by using "all".
    # permissions: a list of roles for channel-based notification services.
    # Message-specific variables for each framework that may be called.

    # call the notification functions
    # global variable for this is in settings.py
    # plugin loading is handled in core.urls
    [func(**kwargs) for func in settings.NOTIFY_FUNCS]


def load_modules():
    res = {}
    # check subfolders
    from utils import notify
    plugin_dir = os.listdir(os.path.join(os.path.dirname(os.path.abspath(notify.__file__)), "notify_plugins"))

    # load the modules
    for f in plugin_dir:
        if f.startswith('.'):
            # Ignore development files
            continue

        f = os.path.splitext(f)[0]

        res[f] = __import__("utils.notify_plugins.{0}".format(f), fromlist=["utils"])

        # plugins without a "plugin_loaded" method will be removed from this dictionary
        # the plugin_loaded method should do whatever is needed for plugin startup
        try:
            res[f].plugin_loaded()
        except BaseException:
            del res[f]

    return res

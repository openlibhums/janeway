#!/usr/bin/env python

import os
import sys

from django.conf import settings

from utils import load_janeway_settings

os.environ.setdefault("JANEWAY_SETTINGS_MODULE", "core.settings")

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    load_janeway_settings()

    execute_from_command_line(sys.argv)

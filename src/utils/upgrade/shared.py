import os
import json

from django.conf import settings

from utils import models


def versions():
    path = os.path.join(settings.BASE_DIR, 'utils', 'upgrade', 'versions.json')
    with open(path, 'r', encoding="utf-8") as f:

        versions = json.loads(f.read())
        return versions


def current_version():
    versions = models.Version.objects.all().order_by('-date')

    if versions:
        return versions[0]

    else:
        pass
        # Its possible that versioning didn't exist as it was only introduced in 1.3.


def set_version(version):
    obj, created = models.Version.objects.get_or_create(number=version)

    if not created:
        print('WARNING: This version was already found so was not created.')


def check_version(script):
    version = current_version()

    if version and version.number == script:
        input('This upgrade appears to have already been run. '
              'Press [Enter] to continue running, press [Ctrl + C] to exit.')

import os
import json

from django.conf import settings

from utils import models


def versions():
    file = open(os.path.join(settings.BASE_DIR, 'utils', 'upgrade', 'versions.json'))

    versions = json.loads(file.read())

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
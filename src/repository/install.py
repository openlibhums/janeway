import os
import codecs
import json

from django.conf import settings


def load_settings(instance, force=True):
    """
    Instance: Repository object instance
    """
    path = os.path.join(
        settings.BASE_DIR,
        'utils/install/repository_settings.json',
    )
    with codecs.open(
            os.path.join(path),
            'r+',
            encoding='utf-8',
    ) as json_data:
        repo_settings = json.load(json_data)

        for key, value in repo_settings[0].items():
            if hasattr(instance, key):
                if force or not getattr(instance, key, None):
                    setattr(instance, key, value)

    return instance

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

        # As we are using pre_save there is no need to call save so we
        # avoid recursion here.
        if force or not instance.submission:
            instance.submission = repo_settings[0]['submission']
        if force or not instance.publication:
            instance.publication = repo_settings[0]['publication']
        if force or not instance.decline:
            instance.decline = repo_settings[0]['decline']
        if force or not instance.accept_version:
            instance.accept_version = repo_settings[0]['accept_version']
        if force or not instance.decline_version:
            instance.decline_version = repo_settings[0]['decline_version']
        if force or not instance.new_comment:
            instance.new_comment = repo_settings[0]['new_comment']

    return instance
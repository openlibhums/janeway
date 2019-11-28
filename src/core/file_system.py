"""
Janeway's File System classes
"""
__copyright__ = "Copyright 2018 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class JanewayFileSystemStorage(FileSystemStorage):
    """ Allows to change settings.MEDIA_ROOT without generating a migration

    :param relative_path: relative path on top of settings.MEDIA_ROOT
    """
    def __init__(self, location=None, *args, **kwargs):
        if location:
            try:
                _, relative_path = location.split(settings.MEDIA_ROOT)
            except ValueError:
                absolute_path = os.path.join(settings.BASE_DIR, location)
                relative_path = os.path.relpath(absolute_path, os.getcwd())
        else:
            relative_path = None
        self.relative_path = relative_path
        super().__init__(location, *args, **kwargs)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.base_url == other.base_url
        )

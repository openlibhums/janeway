import os
import shutil

from django.conf import settings


def copy_file(source, destination):
    """
    :param source: The source of the folder for copying
    :param destination: The destination folder for the file
    :return:
    """

    destination_folder = os.path.join(settings.BASE_DIR, os.path.dirname(destination))

    if not os.path.exists(destination_folder):
        os.mkdir(destination_folder)

    shutil.copy(os.path.join(settings.BASE_DIR, source),
                os.path.join(settings.BASE_DIR, destination))


def build():
    print('Copying Material Theme CSS')
    copy_file('themes/material/assets/material.js', 'static/material/material.js')
    copy_file('themes/material/assets/toc.js', 'static/material/toc.js')
    copy_file('themes/material/assets/sub-toc.js', 'static/material/sub-toc.js')
    copy_file('themes/material/assets/mat.css', 'static/material/mat.css')
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


def create_paths():
    base_path = os.path.join(settings.BASE_DIR, 'static', 'default')
    folders = ['css', 'js']

    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)


def build():
    print('Creating folders')
    create_paths()
    print('Copying CSS')
    copy_file('themes/default/assets/css/bootstrap.css', 'static/default/css/bootstrap.css')
    copy_file('themes/default/assets/js/bootstrap.js', 'static/default/js/bootstrap.js')

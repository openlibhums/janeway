import os
import shutil

from django.conf import settings

from journal import models as journal_models


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
    base_path = os.path.join(settings.BASE_DIR, 'static', 'clean')
    folders = ['css']

    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)


def process_journals():
    journals = journal_models.Journal.objects.all()

    for journal in journals:
        for file in journal.scss_files:
            if file.endswith('clean_override.css'):
                print('Copying material override file for {name}'.format(name=journal.name))
                override_css_dir = os.path.join(settings.BASE_DIR, 'static', 'clean', 'css')
                override_css_file = os.path.join(override_css_dir, 'journal{0}_override.css'.format(str(journal.id)))

                # test if the journal CSS directory exists and create it if not
                os.makedirs(override_css_dir, exist_ok=True)

                # copy file to static
                copy_file(file, override_css_file)


def build():
    print('Creating folders')
    create_paths()
    print('Copying CSS')
    copy_file('themes/clean/assets/css/clean.css', 'static/clean/css/clean.css')
    process_journals()

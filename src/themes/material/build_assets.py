import os
import shutil

from django.conf import settings

from journal import models as journal_models


def press_scss_files():
    try:
        scss_path = os.path.join(settings.BASE_DIR, 'files', 'styling', 'press')
        os.makedirs(scss_path, exist_ok=True)
        return [os.path.join(scss_path, f) for f in os.listdir(scss_path) if os.path.isfile(os.path.join(scss_path, f))]
    except FileNotFoundError:
        return []


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


def process_journals():
    journals = journal_models.Journal.objects.all()

    for journal in journals:
        for file in journal.scss_files:
            if file.endswith('material_override.css'):
                print('Copying material override file for {name}'.format(name=journal.name))
                override_css_dir = os.path.join(settings.BASE_DIR, 'static', 'material', 'css')
                override_css_file = os.path.join(override_css_dir, 'journal{0}_override.css'.format(str(journal.id)))

                # test if the journal CSS directory exists and create it if not
                os.makedirs(override_css_dir, exist_ok=True)

                # copy file to static
                copy_file(file, override_css_file)


def process_press():
    for file in press_scss_files():
        if file.endswith('material_override.css'):
            print('Copying material override file for press')
            override_css_dir = os.path.join(settings.BASE_DIR, 'static', 'material', 'css')
            override_css_file = os.path.join(override_css_dir, 'press_override.css')

            # test if the journal CSS directory exists and create it if not
            os.makedirs(override_css_dir, exist_ok=True)

            # copy file to static
            copy_file(file, override_css_file)


def build():
    print('Copying Material Theme CSS')
    copy_file('themes/material/assets/material.js', 'static/material/material.js')
    copy_file('themes/material/assets/toc.js', 'static/material/toc.js')
    copy_file('themes/material/assets/sub-toc.js', 'static/material/sub-toc.js')
    copy_file('themes/material/assets/mat.css', 'static/material/mat.css')
    process_journals()
    process_press()

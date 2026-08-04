import os
import shutil

from django.conf import settings
from utils import setting_handler


def copy_file(source, destination):
    """
    :param source: The source of the folder for copying
    :param destination: The destination folder for the file
    :return:
    """
    destination_folder = os.path.join(settings.BASE_DIR, os.path.dirname(destination))
    os.makedirs(destination_folder, exist_ok=True)

    shutil.copy(
        os.path.join(settings.BASE_DIR, source),
        os.path.join(settings.BASE_DIR, destination),
    )


def create_paths():
    base_path = os.path.join(settings.BASE_DIR, "static", "clarity")
    folders = ["css", "js"]

    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)



def copy_theme_files():
    """Copy theme CSS and JS files to static directory."""
    theme_files = [
        ("css", "clarity.css"),
        ("css", "light-mode-settings.css"),
        ("css", "palettes.css"),
        ("js", "tooltip-init.js"),
        ("js", "toc.js"),
    ]

    for file_type, filename in theme_files:
        source = os.path.join("themes", "clarity", "assets", file_type, filename)
        destination = os.path.join("static", "clarity", file_type, filename)
        copy_file(source, destination)


def create_settings():
    setting_handler.create_setting(
        setting_group_name='general',
        setting_name='clarity_palette',
        type='text',
        pretty_name='Clarity Palette',
        description='The colour palette for the Clarity theme. Options: evergreen, ocean, cardinal, paper.',
        is_translatable=False,
        default_value='evergreen',
    )


def build():
    print("Creating folders")
    create_paths()

    print("Copying theme files")
    copy_theme_files()

    print("Creating settings")
    create_settings()


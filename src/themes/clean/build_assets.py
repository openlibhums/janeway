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
    os.makedirs(destination_folder, exist_ok=True)

    shutil.copy(
        os.path.join(settings.BASE_DIR, source),
        os.path.join(settings.BASE_DIR, destination),
    )


def create_paths():
    base_path = os.path.join(settings.BASE_DIR, "static", "clean")
    folders = ["css", "js"]

    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)


def process_journals():
    journals = journal_models.Journal.objects.all()

    for journal in journals:
        for file in journal.scss_files:
            if file.endswith("clean_override.css"):
                print(f"Copying clean override file for {journal.name}")

                override_css_file = os.path.join(
                    settings.BASE_DIR,
                    "static",
                    "clean",
                    "css",
                    f"journal{journal.id}_override.css",
                )

                copy_file(file, override_css_file)


def copy_theme_files():
    """Copy theme CSS and JS files to static directory."""
    theme_files = [
        ("css", "clean.css"),
        ("css", "evergreen.css"),
        ("css", "ocean.css"),
        ("css", "cardinal.css"),
        ("css", "midnight.css"),
        ("js", "tooltip-init.js"),
    ]

    for file_type, filename in theme_files:
        source = os.path.join("themes", "clean", "assets", file_type, filename)
        destination = os.path.join("static", "clean", file_type, filename)
        copy_file(source, destination)


def build():
    print("Creating folders")
    create_paths()

    print("Copying theme files")
    copy_theme_files()

    print("Processing journal overrides")
    process_journals()

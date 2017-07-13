import os
import shutil
import sys
import uuid

from django.core.management.base import BaseCommand
from django.core.cache import cache

from journal import models as journal_models
from submission import models as submission_models
from core import models as core_models, files


class Command(BaseCommand):
    """ A management command to update all render galleys from a folder or repo."""

    help = "Update all render galleys from a folder or repo. Dangerous."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--journal_code')
        parser.add_argument('--folder_path')

    def handle(self, *args, **options):
        """ Updates all render galleys from a folder.

        :param args: None
        :param options: None.
        :return: None
        """
        journal_code = options.get('journal_code')
        folder_path = options.get('folder_path')

        try:
            journal = journal_models.Journal.objects.get(code=journal_code)
        except journal_models.Journal.DoesNotExist:
            print('No journal with that code was found.')
            sys.exit()

        journal_folder = os.path.join(folder_path, journal.code)
        if not os.path.isdir(journal_folder):
            print('No directory found.')
            sys.exit()

        article_folders = os.listdir(journal_folder)

        for folder in article_folders:
            try:
                article = submission_models.Article.objects.get(pk=folder)
                print('Article {0} found.'.format(article.pk))

                try:
                    file = os.listdir(os.path.join(journal_folder, folder))[0]
                    print('File {0} found.'.format(file))
                except IndexError:
                    file = None

                if file:
                    if article.render_galley:
                        print('Article already has a render galley, updating it.')
                        article.render_galley.file.unlink_file()
                        shutil.copyfile(os.path.join(journal_folder, folder, file),
                                        article.render_galley.file.self_article_path())
                        print('Existing render galley updated.')
                    else:
                        print('Article does not have a render galley, creating one.')
                        file_object = core_models.File.objects.create(
                            article_id=article.pk,
                            original_filename=file,
                            uuid_filename=uuid.uuid4(),
                            label='Render Galley',
                            privacy='public',
                            mime_type=files.guess_mime(file),
                        )

                        galley_object = core_models.Galley.objects.create(
                            article=article,
                            file=file_object,
                            is_remote=False,
                            label='Render Galley',
                            type=os.path.splitext(file)[1]
                        )

                        article.render_galley = galley_object
                        article.save()
                        print('New file and galley created.')
                else:
                    print('No file was found in folder {0}'.format(folder))
            except submission_models.Article.DoesNotExist:
                print('No article found with ID {0}'.format(folder))

        cache.clear()
        print('Cache cleared.')

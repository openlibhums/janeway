import difflib

from django.core.management.base import BaseCommand, CommandError

from submission import models
from core import files, models as core_models


class Command(BaseCommand):
    """Tests the rendering of an article against the provided XSLFile"""

    help = "Tests the rendering of an article against the provided XSLFile"

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument(
            'xslfile_label',
            help="The label of the XSLFile being tested"
        )
        parser.add_argument(
            'article_id',
            help="The article ID against which the test will be run"
        )

    def handle(self, *args, **options):
        """ Compares the output

        :param args: None
        :param options: None
        :return: None
        """
        try:
            article = models.Article.objects.get(pk=options["article_id"])
            xsl_file = core_models.XSLFile.objects.get(
                label=options["xslfile_label"])
        except models.Article.DoesNotExist:
            raise CommandError("Couldn't find the article")

        except core_models.XSLFile.DoesNotExist:
            raise CommandError("Couldn't find the xsl file")

        xml_galleys = article.galley_set.filter(
            file__mime_type__in=files.XML_MIMETYPES,
        )

        if xml_galleys.exists():

            if xml_galleys.count() > 1:
                print("Found multiple XML galleys for article {id}, "
                      "returning first match".format(id=article.pk))

            xml_galley = xml_galleys[0]
        else:
            raise CommandError("Article doesn't have an XML Galley")

        old_render = str(xml_galley.render())
        new_render = str(files.render_xml(
            xml_galley.file, article,
            xsl_path=xsl_file.file.path,
        ))

        diffs = difflib.ndiff(old_render.splitlines(), new_render.splitlines())
        total_diffs = 0
        for diff in diffs:
            if diff.startswith("-") or diff.startswith("+"):
                total_diffs += 1
                print(diff)
        print(80*"=")
        print("Found %s diffs" % total_diffs)

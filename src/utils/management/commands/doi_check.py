import requests

from django.core.management.base import BaseCommand
from django.utils import timezone

from journal import models as journal_models
from cron import models as cron_models
from submission import models as submission_models
from identifiers import models as ident_models
from utils import setting_handler


class Command(BaseCommand):
    """
    Checks that DOIs resolve correctly.
    """

    help = "Deletes duplicate settings."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code', nargs='?', default=None)

    def handle(self, *args, **options):
        """Runs through articles and checks their DOIs resolve.

        :param args: None
        :param options: None
        :return: None
        """
        if options.get('journal_code'):
            journals = journal_models.Journal.objects.filter(code=options.get('journal_code'))
        else:
            journals = journal_models.Journal.objects.all()
        request = cron_models.Request()

        for journal in journals:
            try:
                request.secure = setting_handler.get_setting('general', 'is_secure', journal)
            except IndexError:
                request.secure = False

            print('Processing {0}'.format(journal.name))
            articles = submission_models.Article.objects.filter(journal=journal)

            for article in articles:
                doi = article.get_identifier('doi', object=True)

                if doi and doi.is_doi:
                    print('Article {0} with DOI {1} processing.'.format(article.pk, doi))

                    should_resolve_to = "{0}{1}".format(journal.full_url(request), article.local_url)
                    resolves_to = requests.get(doi.get_doi_url())

                    if not should_resolve_to == resolves_to.url:
                        print('Failure detected.')
                        print(should_resolve_to, resolves_to.url)

                        o, c = ident_models.BrokenDOI.objects.get_or_create(
                            identifier=doi,
                            article=article,
                            defaults={'checked': timezone.now(),
                                      'resolves_to': resolves_to.url,
                                      'expected_to_resolve_to': should_resolve_to}
                        )

                        if c:
                            print('This failure is new \n')
                        else:
                            print('This failure has previously been detected \n')
                    else:
                        try:
                            ident_models.BrokenDOI.objects.get(identifier=doi).delete()
                        except ident_models.BrokenDOI.DoesNotExist:
                            pass

                else:
                    print('Article {0} has no DOI, skipping \n'.format(article.pk))

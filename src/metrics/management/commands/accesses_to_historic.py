import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core import serializers

from metrics import models


class Command(BaseCommand):
    """
    A management command that tidies up access records into historic accesses after 24 months has passed (COUNTER)
    """

    help = "Tidies ArticleAccess objects into HistoricArticleAccess params."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--dump_data', action='store_true', default=False)

    def handle(self, *args, **options):
        """Tidies up access records into historic accesses after 24 months has passed (COUNTER).

        :param args: None
        :param options: None
        :return: None
        """
        date_to_tidy = timezone.now() - timedelta(weeks=104)

        article_accesses = models.ArticleAccess.objects.filter(accessed__lte=date_to_tidy)

        if options.get('dump_data') and article_accesses:
            path = os.path.join(settings.BASE_DIR, 'files', 'data_backup', date_to_tidy.strftime('%Y-%m-%d %H:%M'))
            if not os.path.exists(path):
                os.makedirs(path)
            with open(os.path.join(path, 'article_accesses.json'), 'w+') as f:
                data = serializers.serialize("json", article_accesses, indent=4)
                f.write(data)

        for access in article_accesses:

            if access.type == 'view':
                access.article.historicarticleaccess.add_one_view()
            elif access.type == 'download':
                access.article.historicarticleaccess.add_one_download()

            access.delete()

from django.db import connection
from django.db.utils import OperationalError
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings

from utils.logger import get_logger

logger = get_logger(__name__)


FT_SEARCH_TRANSLATABLE_COLUMNS = {
        ('submission_article', 'title'),
        ('submission_article', 'abstract'),
}


FT_SEARCH_COLUMNS = {
        ('submission_frozenauthor', 'first_name'),
        ('submission_frozenauthor', 'last_name'),
        ('submission_keyword', 'word'),
        ('core_filetext', 'contents'),
}


class Command(BaseCommand):
    """ A management that generates search indexes"""

    help = "Generates database indexes for full text search (idempotent)"

    def handle(self, *args, **options):
        if not settings.ENABLE_FULL_TEXT_SEARCH:
            logger.info('Full Text search not enabled')
            return
        cursor = connection.cursor()
        if connection.vendor == "mysql":
            for table, col in self.get_charfield_columns():
                sql = f"CREATE FULLTEXT INDEX {col}_ft_idx on {table}({col})"
                logger.debug("running SQL: %s", sql)
                try:
                    cursor.execute(sql)
                except OperationalError as e:
                        pass # Ignore duplicate indexes

    def get_charfield_columns(self):
        for column in FT_SEARCH_COLUMNS:
            yield column

        for table, col in FT_SEARCH_TRANSLATABLE_COLUMNS:
            for lang, _ in settings.LANGUAGES:
                yield table, f'{col}_{lang}'



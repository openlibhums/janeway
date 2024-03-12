from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
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

    INDEXING_SQL_TEMPLATES = {
        # We use GIN over GiST indexes as the former are more performant during
        # Lookups at the expense of lower build/update performance 
        # https://www.postgresql.org/docs/current/textsearch-indexes.html
        "postgresql": "CREATE INDEX {idx_name} ON {table} USING gin({col});",
        "mysql": "CREATE FULLTEXT INDEX {idx_name} on {table}({col});",
    }

    def handle(self, *args, **options):
        if not settings.ENABLE_FULL_TEXT_SEARCH:
            logger.info('Full Text search not enabled')
            return
        cursor = connection.cursor()
        if connection.vendor in self.INDEXING_SQL_TEMPLATES:
            if connection.vendor == "postgresql":
                try:
                    cursor.execute("CREATE EXTENSION btree_gin;")
                except ProgrammingError:
                    pass # Ignore if already exists

            for table, col in self.get_columns_to_index(connection.vendor):
                idx_name = f"{col}_ft_idx"
                sql = self.INDEXING_SQL_TEMPLATES[connection.vendor].format(
                    col=col,
                    table=table,
                    idx_name=idx_name
                )
                logger.debug("running SQL: %s", sql)
                try:
                    cursor.execute(sql)
                except (OperationalError, ProgrammingError) as e:
                    pass # Ignore if already exists
        else:
            logger.warning(
                "Full-text indexing on %s backend not supported",
                connection.vendor,
            )

    def get_columns_to_index(self, vendor):
        for table, col in FT_SEARCH_COLUMNS:
            if table == "core_filetext" and vendor =="postgresql":
                continue
            yield table, col

        for table, col in FT_SEARCH_TRANSLATABLE_COLUMNS:
            for lang, _ in settings.LANGUAGES:
                yield table, f'{col}_{lang}'



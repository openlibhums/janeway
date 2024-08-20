from django.db import connection
from django.db.models import Aggregate, TextField


class GroupConcat(Aggregate):
    """
    Custom db function to concatenate values from a queryset into a single
    string.

    Supports PostgresSQL, MSSQL, MySQL, MariaDB, and SQLite.
    Note:
        MariaDB does not have its own vendor string and is covered by MySQL

    Usage:
        articles_with_authors = Article.objects.annotate(
            author_names=GroupConcat(
                Concat(
                    F('author__first_name'),
                    Value(' '),
                    F('author__last_name')
                ),
                separator='; '  # can be added to override default comma
            )
        )

    Raises:
        NotImplementedError: If the given database backend is not supported.
    """

    output_field = TextField()

    def __init__(self, expression, separator=', ', distinct=False, **extra):
        super().__init__(expression, distinct=distinct, **extra)
        self.extra['separator'] = separator
        self.vendor = connection.vendor

        if self.vendor == 'postgresql':
            self.function = 'STRING_AGG'
            self.template = "%(function)s(%(distinct)s%(expressions)s, '%(separator)s')"
        elif self.vendor == 'mysql':
            self.function = 'GROUP_CONCAT'
            self.template = "%(function)s(%(distinct)s%(expressions)s SEPARATOR '%(separator)s')"
        elif self.vendor == 'sqlite':
            self.function = 'GROUP_CONCAT'
            self.template = "%(function)s(%(expressions)s, '%(separator)s')"
        elif self.vendor == 'mssql':
            self.function = 'STRING_AGG'
            self.template = "%(function)s(%(expressions)s, '%(separator)s')"
        else:
            raise NotImplementedError(
                f"{self.vendor} is not supported for GroupConcat"
            )

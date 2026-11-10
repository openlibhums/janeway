from django.db import migrations

# GIN indexes for repository search. Each expression matches the one
# PreprintSearchManager.build_postgres_lookups builds, config included: the
# planner only uses an expression index when the expression is identical.
INDEXES = (
    (
        "repository_preprint_title_search_gin",
        """
        CREATE INDEX IF NOT EXISTS {name} ON repository_preprint USING GIN (
            setweight(to_tsvector('english'::regconfig, COALESCE(title, '')), 'A')
        )
        """,
    ),
    (
        "repository_preprint_abstract_search_gin",
        """
        CREATE INDEX IF NOT EXISTS {name} ON repository_preprint USING GIN (
            setweight(to_tsvector('english'::regconfig, COALESCE(abstract, '')), 'C')
        )
        """,
    ),
    (
        # Lives in the repository app because it serves repository search.
        "submission_frozenauthor_name_search_gin",
        """
        CREATE INDEX IF NOT EXISTS {name} ON submission_frozenauthor USING GIN (
            to_tsvector(
                'simple'::regconfig,
                COALESCE(last_name, '') || ' ' || COALESCE(first_name, '')
            )
        )
        """,
    ),
)


def create_indexes(apps, schema_editor):
    """Postgres only: Janeway also runs on MySQL and SQLite, which have no
    tsvector, and search there uses its own lookups."""
    if schema_editor.connection.vendor != "postgresql":
        return
    for name, sql in INDEXES:
        schema_editor.execute(sql.format(name=name))


def drop_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    for name, _sql in INDEXES:
        schema_editor.execute("DROP INDEX IF EXISTS {}".format(name))


class Migration(migrations.Migration):
    dependencies = [
        ("repository", "0064_peer_reviewed_submission_file_required"),
        ("submission", "0094_remove_creditrecord_preprint_author"),
    ]

    operations = [
        migrations.RunPython(create_indexes, drop_indexes),
    ]

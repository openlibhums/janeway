from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("repository", "0060_version_metadata"),
        ("submission", "0092_merge_20261007_1107"),
    ]

    operations = [
        migrations.AddField(
            model_name="frozenauthor",
            name="preprint",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="repository.preprint",
            ),
        ),
        migrations.AddField(
            model_name="frozenauthor",
            name="preprint_version",
            field=models.ForeignKey(
                blank=True,
                help_text="Set when this record is part of the author list of a superseded preprint version.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="repository.preprintversion",
            ),
        ),
        migrations.AddField(
            model_name="frozenauthor",
            name="version_queue",
            field=models.ForeignKey(
                blank=True,
                help_text="Set when this record is on the author list of a preprint update.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="repository.versionqueue",
            ),
        ),
        migrations.AddConstraint(
            model_name="frozenauthor",
            constraint=models.UniqueConstraint(
                fields=("preprint", "author"),
                name="unique_account_per_preprint_author_list",
            ),
        ),
        migrations.AddConstraint(
            model_name="frozenauthor",
            constraint=models.UniqueConstraint(
                fields=("version_queue", "author"),
                name="unique_account_per_update_author_list",
            ),
        ),
        migrations.AddConstraint(
            model_name="frozenauthor",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("article__isnull", False),
                        ("preprint__isnull", True),
                        ("preprint_version__isnull", True),
                        ("version_queue__isnull", True),
                    ),
                    models.Q(
                        ("preprint__isnull", False),
                        ("article__isnull", True),
                        ("preprint_version__isnull", True),
                        ("version_queue__isnull", True),
                    ),
                    models.Q(
                        ("preprint_version__isnull", False),
                        ("article__isnull", True),
                        ("preprint__isnull", True),
                        ("version_queue__isnull", True),
                    ),
                    models.Q(
                        ("version_queue__isnull", False),
                        ("article__isnull", True),
                        ("preprint__isnull", True),
                        ("preprint_version__isnull", True),
                    ),
                    models.Q(
                        ("article__isnull", True),
                        ("preprint__isnull", True),
                        ("preprint_version__isnull", True),
                        ("version_queue__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="exclusive_fields_frozen_author_article_preprint_preprint_ver0a48",
            ),
        ),
    ]

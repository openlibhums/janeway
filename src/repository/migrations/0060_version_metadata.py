from django.db import migrations, models
import django.db.models.deletion


def delete_version_and_proposed_answers(apps, schema_editor):
    """
    Before reversing, remove answers that belong to a version snapshot or a
    pending update, since answers must belong to a preprint again.
    """
    RepositoryFieldAnswer = apps.get_model("repository", "RepositoryFieldAnswer")
    RepositoryFieldAnswer.objects.filter(preprint__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("repository", "0059_preprint_title_bleach"),
    ]

    operations = [
        migrations.AddField(
            model_name="preprintversion",
            name="metadata_frozen",
            field=models.BooleanField(
                default=False,
                help_text="Whether this version's authors and custom field answers were snapshotted when it was superseded. Versions superseded before snapshots existed show the preprint's current metadata.",
            ),
        ),
        migrations.AddField(
            model_name="repositoryfieldanswer",
            name="preprint_version",
            field=models.ForeignKey(
                blank=True,
                help_text="Set when this answer is part of a superseded version's snapshot.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="repository.preprintversion",
            ),
        ),
        migrations.AddField(
            model_name="repositoryfieldanswer",
            name="version_queue",
            field=models.ForeignKey(
                blank=True,
                help_text="Set when this answer is proposed by a pending update.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="repository.versionqueue",
            ),
        ),
        migrations.AddField(
            model_name="versionqueue",
            name="changed_sections",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="The sections the author changed (title, abstract, published_doi, file, authors, field_answers); approving replaces these.",
            ),
        ),
        migrations.AlterField(
            model_name="repositoryfieldanswer",
            name="preprint",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="repository.preprint",
            ),
        ),
        migrations.AddConstraint(
            model_name="repositoryfieldanswer",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("preprint__isnull", False),
                        ("preprint_version__isnull", True),
                        ("version_queue__isnull", True),
                    ),
                    models.Q(
                        ("preprint_version__isnull", False),
                        ("preprint__isnull", True),
                        ("version_queue__isnull", True),
                    ),
                    models.Q(
                        ("version_queue__isnull", False),
                        ("preprint__isnull", True),
                        ("preprint_version__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="exclusive_fields_repository_field_answer_preprint_preprint_v3564",
            ),
        ),
        migrations.AddField(
            model_name="versionqueue",
            name="started_from",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="A checksum of each section of the preprint's metadata when this update was started.",
            ),
        ),
        migrations.AddField(
            model_name="versionqueue",
            name="is_draft",
            field=models.BooleanField(
                default=False,
                help_text="Drafts are still being prepared by the author and are not in the moderation queue.",
            ),
        ),
        migrations.AlterField(
            model_name="preprint",
            name="doi",
            field=models.CharField(
                blank=True,
                help_text="You can add a DOI linking to this item's published version using this field. Please provide the full DOI ie. https://doi.org/10.1017/CBO9781316161012.",
                max_length=255,
                null=True,
                verbose_name="Published DOI",
            ),
        ),
        migrations.RunPython(
            migrations.RunPython.noop,
            reverse_code=delete_version_and_proposed_answers,
        ),
    ]

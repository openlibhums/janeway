from django.db import migrations

LICENCE_FIELDS = (
    "name",
    "short_name",
    "url",
    "text",
    "order",
    "available_for_submission",
)


def press_copy(Licence, licence, press):
    match = Licence.objects.filter(
        journal__isnull=True,
        press=press,
        short_name=licence.short_name,
        url=licence.url,
    ).first()
    if match:
        return match
    return Licence.objects.create(
        press=press,
        **{field: getattr(licence, field) for field in LICENCE_FIELDS},
    )


def move_journal_licences(apps, schema_editor):
    """
    Repositories offer press-level licences, but some were set up offering a
    journal's licences. Give each one a press-level copy and move the
    repository's offer and its preprints over to it.
    """
    Repository = apps.get_model("repository", "Repository")
    Preprint = apps.get_model("repository", "Preprint")
    Licence = apps.get_model("submission", "Licence")

    for repository in Repository.objects.all():
        pks = set(
            Preprint.objects.filter(
                repository=repository,
                license__journal__isnull=False,
            ).values_list("license", flat=True)
        ) | set(
            repository.active_licenses.filter(journal__isnull=False).values_list(
                "pk", flat=True
            )
        )
        for licence in Licence.objects.filter(pk__in=pks):
            copy = press_copy(Licence, licence, repository.press)
            if repository.active_licenses.filter(pk=licence.pk).exists():
                repository.active_licenses.remove(licence)
                repository.active_licenses.add(copy)
            Preprint.objects.filter(
                repository=repository,
                license=licence,
            ).update(license=copy)


class Migration(migrations.Migration):
    dependencies = [
        ("repository", "0076_host_ror_id"),
        ("submission", "0095_funding_for_preprints"),
    ]

    operations = [
        migrations.RunPython(
            move_journal_licences,
            reverse_code=migrations.RunPython.noop,
        ),
    ]

from django.db import migrations
from django.db.models import Q

AFFILIATION_FIELDS = (
    "title",
    "department",
    "organization_id",
    "is_primary",
    "start",
    "end",
)


def preprint_authors_to_frozen_authors(apps, schema_editor):
    """
    Copies each PreprintAuthor onto the preprint's working author list as a
    FrozenAuthor, moving its affiliations and CRediT records across.
    PreprintAuthors whose account was deleted were never displayed, so they
    are not copied.
    """
    PreprintAuthor = apps.get_model("repository", "PreprintAuthor")
    FrozenAuthor = apps.get_model("submission", "FrozenAuthor")
    ControlledAffiliation = apps.get_model("core", "ControlledAffiliation")
    CreditRecord = apps.get_model("submission", "CreditRecord")

    preprint_authors = PreprintAuthor.objects.filter(
        account__isnull=False,
    ).select_related("account")
    for preprint_author in preprint_authors.iterator():
        account = preprint_author.account
        frozen_author = FrozenAuthor.objects.create(
            preprint_id=preprint_author.preprint_id,
            author=account,
            name_prefix=account.salutation or "",
            first_name=account.first_name or "",
            middle_name=account.middle_name or "",
            last_name=account.last_name or "",
            name_suffix=account.suffix or "",
            order=preprint_author.order,
        )

        moved = ControlledAffiliation.objects.filter(
            preprint_author_id=preprint_author.pk,
        ).update(frozen_author_id=frozen_author.pk, preprint_author_id=None)
        if not moved:
            # Preprint authors without their own affiliation displayed the
            # account's, so keep showing that.
            for affiliation in ControlledAffiliation.objects.filter(
                account_id=account.pk,
            ):
                ControlledAffiliation.objects.create(
                    frozen_author_id=frozen_author.pk,
                    **{
                        field: getattr(affiliation, field)
                        for field in AFFILIATION_FIELDS
                    },
                )

        # CreditRecord is unique per frozen author and role, which was not
        # enforced for preprint authors, so move one record per role.
        seen_roles = set()
        for credit in CreditRecord.objects.filter(
            preprint_author_id=preprint_author.pk,
        ).order_by("pk"):
            if credit.role in seen_roles:
                credit.delete()
                continue
            seen_roles.add(credit.role)
            CreditRecord.objects.filter(pk=credit.pk).update(
                frozen_author_id=frozen_author.pk,
                preprint_author_id=None,
            )

    # Authors whose account was deleted were never displayed and are not
    # copied; remove their affiliations and credits rather than leave
    # records that belong to nothing.
    orphans = PreprintAuthor.objects.filter(account__isnull=True).values("pk")
    ControlledAffiliation.objects.filter(preprint_author_id__in=orphans).delete()
    CreditRecord.objects.filter(preprint_author_id__in=orphans).delete()


def frozen_authors_to_preprint_authors(apps, schema_editor):
    """
    Restores PreprintAuthors from the working author lists. Authors without
    an account and superseded version snapshots cannot be represented and
    are dropped.
    """
    PreprintAuthor = apps.get_model("repository", "PreprintAuthor")
    FrozenAuthor = apps.get_model("submission", "FrozenAuthor")
    ControlledAffiliation = apps.get_model("core", "ControlledAffiliation")
    CreditRecord = apps.get_model("submission", "CreditRecord")

    working_authors = FrozenAuthor.objects.filter(
        preprint__isnull=False,
        preprint_version__isnull=True,
        author__isnull=False,
    )
    for frozen_author in working_authors.iterator():
        preprint_author, _created = PreprintAuthor.objects.get_or_create(
            preprint_id=frozen_author.preprint_id,
            account_id=frozen_author.author_id,
            defaults={"order": frozen_author.order},
        )
        ControlledAffiliation.objects.filter(
            frozen_author_id=frozen_author.pk,
        ).update(preprint_author_id=preprint_author.pk, frozen_author_id=None)
        CreditRecord.objects.filter(
            frozen_author_id=frozen_author.pk,
        ).update(preprint_author_id=preprint_author.pk, frozen_author_id=None)

    # Delete all preprint authors (working lists, version snapshots and
    # pending update proposals), with their affiliations and CRediT records.
    # QuerySet.delete() cannot collect the cascade across these historical
    # models, so do it explicitly.
    preprint_frozen_authors = FrozenAuthor.objects.filter(
        Q(preprint__isnull=False)
        | Q(preprint_version__isnull=False)
        | Q(version_queue__isnull=False)
    )
    ControlledAffiliation.objects.filter(
        frozen_author_id__in=preprint_frozen_authors.values("pk"),
    ).delete()
    CreditRecord.objects.filter(
        frozen_author_id__in=preprint_frozen_authors.values("pk"),
    ).delete()
    preprint_frozen_authors._raw_delete(schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0115_merge_20260710_1655"),
        ("repository", "0060_version_metadata"),
        ("submission", "0093_frozenauthor_preprint"),
    ]

    operations = [
        migrations.RunPython(
            preprint_authors_to_frozen_authors,
            reverse_code=frozen_authors_to_preprint_authors,
        ),
    ]

"""
Move the answers the OAI importer kept in custom repository fields into
their proper places, and remove those fields:

- Publisher, Source (ISSN/ISBN), Language, Citation and Contributors /
  Editors go into PublicationDetails.
- Licence sets the record's built-in licence, if it has none and the text
  matches one of the press's licences.
- Version sets the current file's document version, if it has none.
- Related URLs become additional files (links).
- Free to read is dropped: a file's access says that now.

Only repositories the importer populated are touched: those with its
"Source (ISSN/ISBN)" or "Free to read" field.
"""

import re

from django.db import migrations

PUBLISHER = "Publisher"
SOURCE = "Source (ISSN/ISBN)"
LANGUAGE = "Language"
VERSION = "Version"
FREE_TO_READ = "Free to read"
LICENCE = "Licence"
CITATION = "Citation"
RELATED_URLS = "Related URLs"
EDITORS = "Contributors / Editors"
IMPORTER_FIELDS = (
    PUBLISHER,
    SOURCE,
    LANGUAGE,
    VERSION,
    FREE_TO_READ,
    LICENCE,
    CITATION,
    RELATED_URLS,
    EDITORS,
)
MARKERS = (SOURCE, FREE_TO_READ)
VERSIONS = {
    "am": "accepted",
    "accepted": "accepted",
    "vor": "published",
    "published": "published",
    "smur": "submitted",
    "ao": "submitted",
    "submitted": "submitted",
}


def isbn_or_issn(value):
    digits = re.sub(r"[^0-9Xx]", "", value)
    return "isbn" if len(digits) in (10, 13) else "issn"


def move_answers(apps, schema_editor):
    RepositoryField = apps.get_model("repository", "RepositoryField")
    RepositoryFieldAnswer = apps.get_model("repository", "RepositoryFieldAnswer")
    PublicationDetails = apps.get_model("repository", "PublicationDetails")
    PreprintVersion = apps.get_model("repository", "PreprintVersion")
    PreprintSupplementaryFile = apps.get_model(
        "repository", "PreprintSupplementaryFile"
    )
    Licence = apps.get_model("submission", "Licence")

    repository_ids = (
        RepositoryField.objects.filter(name__in=MARKERS)
        .values_list("repository_id", flat=True)
        .distinct()
    )
    for repository_id in repository_ids:
        fields = list(
            RepositoryField.objects.filter(
                repository_id=repository_id, name__in=IMPORTER_FIELDS
            ).select_related("repository")
        )
        if not fields:
            continue
        press_id = fields[0].repository.press_id
        licences = list(Licence.objects.filter(press_id=press_id)) + list(
            Licence.objects.filter(press__isnull=True, journal__isnull=True)
        )

        answers = (
            RepositoryFieldAnswer.objects.filter(field__in=fields)
            .select_related("field", "preprint")
            .order_by("pk")
        )
        details_by_owner = {}
        for answer in answers.iterator():
            text = (answer.answer or "").strip()
            if not text:
                continue
            name = answer.field.name
            if answer.preprint_id:
                owner = {"preprint_id": answer.preprint_id}
            elif answer.preprint_version_id:
                owner = {"preprint_version_id": answer.preprint_version_id}
            elif answer.version_queue_id:
                owner = {"version_queue_id": answer.version_queue_id}
            else:
                continue
            key = tuple(owner.items())

            if name in (PUBLISHER, SOURCE, LANGUAGE, CITATION, EDITORS):
                details = details_by_owner.get(key)
                if details is None:
                    details = PublicationDetails.objects.filter(**owner).first() or (
                        PublicationDetails(**owner)
                    )
                    details_by_owner[key] = details
                if name == PUBLISHER:
                    details.publisher = text[:500]
                elif name == SOURCE:
                    setattr(details, isbn_or_issn(text), text[:100])
                elif name == LANGUAGE:
                    details.language = text[:50]
                elif name == CITATION:
                    details.citation = text
                elif name == EDITORS:
                    details.editors = text
                continue

            # The rest only apply to a record's current answers.
            preprint = answer.preprint
            if preprint is None:
                continue
            if name == LICENCE and preprint.license_id is None:
                lowered = text.lower().rstrip("/")
                match = next(
                    (
                        licence
                        for licence in licences
                        if lowered
                        in (
                            licence.url.lower().rstrip("/"),
                            licence.name.lower(),
                            licence.short_name.lower(),
                        )
                    ),
                    None,
                )
                if match:
                    preprint.license_id = match.pk
                    preprint.save(update_fields=["license"])
            elif name == VERSION:
                version = VERSIONS.get(text.lower())
                current = (
                    PreprintVersion.objects.filter(preprint=preprint)
                    .order_by("-version", "-date_time", "-id")
                    .select_related("file")
                    .first()
                )
                if (
                    version
                    and current
                    and current.file
                    and not current.file.document_version
                ):
                    current.file.document_version = version
                    current.file.save(update_fields=["document_version"])
            elif name == RELATED_URLS:
                existing = set(
                    PreprintSupplementaryFile.objects.filter(
                        preprint=preprint
                    ).values_list("url", flat=True)
                )
                order = PreprintSupplementaryFile.objects.filter(
                    preprint=preprint
                ).count()
                for url in (line.strip() for line in text.splitlines()):
                    if not url or url in existing:
                        continue
                    PreprintSupplementaryFile.objects.create(
                        preprint=preprint, url=url[:200], label=url[:200], order=order
                    )
                    existing.add(url)
                    order += 1

        for details in details_by_owner.values():
            details.save()

        # Their answers go with them.
        RepositoryField.objects.filter(pk__in=[field.pk for field in fields]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("repository", "0074_publication_details"),
        ("submission", "0095_funding_for_preprints"),
    ]

    operations = [
        migrations.RunPython(move_answers, migrations.RunPython.noop),
    ]

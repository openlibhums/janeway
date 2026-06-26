# Generated migration to explicitly set existing pages to is_draft=False

from django.db import migrations


def set_existing_pages_not_draft(apps, schema_editor):
    Page = apps.get_model("cms", "Page")
    Page.objects.all().update(is_draft=False)


def reverse_operation(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0025_alter_historicalpage_is_draft_alter_page_is_draft"),
    ]

    operations = [
        migrations.RunPython(set_existing_pages_not_draft, reverse_operation),
    ]

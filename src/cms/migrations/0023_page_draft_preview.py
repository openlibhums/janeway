from uuid import uuid4

from django.db import migrations, models


def assign_unique_preview_tokens(apps, schema_editor):
    # A migration's callable default is evaluated once for the whole
    # AddField operation, not once per row, so without this every
    # pre-existing page would be backfilled with the same token.
    Page = apps.get_model("cms", "Page")
    pages = list(Page.objects.all())
    for page in pages:
        page.preview_token = str(uuid4())
    Page.objects.bulk_update(pages, ["preview_token"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0022_navigationitem_nav_item_has_either_link_or_sub_nav"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="is_draft",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="page",
            name="preview_token",
            field=models.CharField(blank=True, default=uuid4, max_length=100),
        ),
        migrations.AddField(
            model_name="historicalpage",
            name="is_draft",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="historicalpage",
            name="preview_token",
            field=models.CharField(blank=True, default=uuid4, max_length=100),
        ),
        migrations.RunPython(assign_unique_preview_tokens, migrations.RunPython.noop),
    ]

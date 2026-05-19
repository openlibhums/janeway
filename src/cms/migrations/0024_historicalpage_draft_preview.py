from uuid import uuid4

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0023_page_draft_preview"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalpage",
            name="is_draft",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="historicalpage",
            name="preview_token",
            field=models.CharField(blank=True, default=uuid4, max_length=100),
        ),
    ]

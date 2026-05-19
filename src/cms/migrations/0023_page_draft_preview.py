from uuid import uuid4

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0022_navigationitem_nav_item_has_either_link_or_sub_nav"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="is_draft",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="page",
            name="preview_token",
            field=models.CharField(blank=True, default=uuid4, max_length=100),
        ),
    ]

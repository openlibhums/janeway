from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0112_add_account_accessibility_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="text_format_preferences",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "Reading options (font, colour scheme, dark mode, italics "
                    "and text size) chosen via the reading options bar, stored "
                    "so they persist between visits."
                ),
                verbose_name="Reading options preferences",
            ),
        ),
    ]

# Generated by Django 3.2.16 on 2023-01-26 13:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("journal", "0055_issue_isbn"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="issueeditor",
            options={"ordering": ("sequence", "account")},
        ),
        migrations.AddField(
            model_name="issueeditor",
            name="sequence",
            field=models.PositiveIntegerField(
                default=1, help_text="Provides for ordering of the Issue Editors."
            ),
        ),
    ]

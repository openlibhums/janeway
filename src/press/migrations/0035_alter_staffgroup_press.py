# Generated by Django 3.2.20 on 2024-05-01 15:47

import core.model_utils
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("press", "0034_merge_20240315_1649"),
    ]

    operations = [
        migrations.AlterField(
            model_name="staffgroup",
            name="press",
            field=models.ForeignKey(
                default=core.model_utils.default_press_id,
                on_delete=django.db.models.deletion.CASCADE,
                to="press.press",
            ),
        ),
    ]

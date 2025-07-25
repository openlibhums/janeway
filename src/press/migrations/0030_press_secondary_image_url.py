# Generated by Django 3.2.18 on 2023-04-24 14:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("press", "0029_press_secondary_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="press",
            name="secondary_image_url",
            field=models.URLField(
                blank=True, help_text="Turns secondary image into a link.", null=True
            ),
        ),
    ]

# Generated by Django 3.2.20 on 2024-06-11 10:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0089_update_setting_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="settingvalue",
            name="value",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="settingvalue",
            name="value_cy",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="settingvalue",
            name="value_de",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="settingvalue",
            name="value_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="settingvalue",
            name="value_en_us",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="settingvalue",
            name="value_fr",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="settingvalue",
            name="value_nl",
            field=models.TextField(blank=True, null=True),
        ),
    ]

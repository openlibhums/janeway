# Generated by Django 4.2.15 on 2024-11-28 10:27

import core.model_utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submission', '0081_auto_20240927_1021'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='abstract_es',
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='article',
            name='title_es',
            field=core.model_utils.JanewayBleachCharField(help_text='Your article title', max_length=999, null=True),
        ),
        migrations.AddField(
            model_name='section',
            name='name_es',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='section',
            name='plural_es',
            field=models.CharField(blank=True, help_text='Pluralised name for the section (e.g: Article -> Articles)', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='submissionconfiguration',
            name='submission_file_text_es',
            field=models.CharField(default='Manuscript File', help_text='During submission the author will be asked to upload a filethat is considered the main text of the article. You can usethis field to change the label for that file in submission.', max_length=255, null=True),
        ),
    ]
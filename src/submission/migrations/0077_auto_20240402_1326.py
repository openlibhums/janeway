# Generated by Django 3.2.20 on 2024-04-02 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submission', '0076_auto_20240402_1301'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Funder',
            new_name='ArticleFunding',
        ),
        migrations.RemoveField(
            model_name='article',
            name='funders',
        ),
    ]
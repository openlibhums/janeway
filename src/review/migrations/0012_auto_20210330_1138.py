# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-03-30 11:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("review", "0011_keep_answers_on_form_delete"),
    ]

    operations = [
        migrations.AddField(
            model_name="decisiondraft",
            name="revision_request_due_date",
            field=models.DateTimeField(
                blank=True,
                help_text="Stores a due date for a Drafted Revision Request.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="decisiondraft",
            name="decision",
            field=models.CharField(
                choices=[
                    ("accept", "Accept Without Revisions"),
                    ("minor_revisions", "Minor Revisions Required"),
                    ("major_revisions", "Major Revisions Required"),
                    ("reject", "Reject"),
                ],
                max_length=100,
                verbose_name="Recommendation",
            ),
        ),
        migrations.AlterField(
            model_name="decisiondraft",
            name="email_message",
            field=models.TextField(
                blank=True,
                help_text="This is a draft of the email that will be sent to the author.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="reviewassignment",
            name="decision",
            field=models.CharField(
                blank=True,
                choices=[
                    ("accept", "Accept Without Revisions"),
                    ("minor_revisions", "Minor Revisions Required"),
                    ("major_revisions", "Major Revisions Required"),
                    ("reject", "Reject"),
                ],
                max_length=20,
                null=True,
                verbose_name="Recommendation",
            ),
        ),
    ]

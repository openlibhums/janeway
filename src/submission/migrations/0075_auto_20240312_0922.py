# Generated by Django 3.2.20 on 2024-03-12 09:22

import core.model_utils
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("submission", "0074_auto_20240212_1537"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="abstract",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="abstract_cy",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="abstract_de",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="abstract_en",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="abstract_en_us",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="abstract_fr",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="abstract_nl",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="article_agreement",
            field=core.model_utils.JanewayBleachField(default=""),
        ),
        migrations.AlterField(
            model_name="article",
            name="comments_editor",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="Add any comments you'd like the editor to consider here.",
                null=True,
                verbose_name="Comments to the Editor",
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="competing_interests",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="If you have any conflict of interests in the publication of this article please state them here.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="custom_how_to_cite",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="Custom 'how to cite' text. To be used only if the block generated by Janeway is not suitable.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="non_specialist_summary",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="A summary of the article for non specialists.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="rights",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="A custom statement on the usage rights for this article and associated materials, to be rendered in the article page",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="title",
            field=core.model_utils.JanewayBleachCharField(
                help_text="Your article title", max_length=999
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="title_cy",
            field=core.model_utils.JanewayBleachCharField(
                help_text="Your article title", max_length=999, null=True
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="title_de",
            field=core.model_utils.JanewayBleachCharField(
                help_text="Your article title", max_length=999, null=True
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="title_en",
            field=core.model_utils.JanewayBleachCharField(
                help_text="Your article title", max_length=999, null=True
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="title_en_us",
            field=core.model_utils.JanewayBleachCharField(
                help_text="Your article title", max_length=999, null=True
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="title_fr",
            field=core.model_utils.JanewayBleachCharField(
                help_text="Your article title", max_length=999, null=True
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="title_nl",
            field=core.model_utils.JanewayBleachCharField(
                help_text="Your article title", max_length=999, null=True
            ),
        ),
        migrations.AlterField(
            model_name="fieldanswer",
            name="answer",
            field=core.model_utils.JanewayBleachField(),
        ),
        migrations.AlterField(
            model_name="frozenauthor",
            name="frozen_biography",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The author's biography at the time they published the linked article. For this article only, it overrides any main biography attached to the author's account. If Frozen Biography is left blank, any main biography for the account will be populated instead.",
                null=True,
                verbose_name="Frozen Biography",
            ),
        ),
        migrations.AlterField(
            model_name="licence",
            name="text",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="note",
            name="text",
            field=core.model_utils.JanewayBleachField(),
        ),
        migrations.AlterField(
            model_name="publishernote",
            name="text",
            field=core.model_utils.JanewayBleachField(max_length=4000),
        ),
    ]

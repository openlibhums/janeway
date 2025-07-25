# Generated by Django 3.2.20 on 2024-03-12 09:22

import core.model_utils
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0015_historicalpage"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="historicalpage",
            name="support_copy_paste",
        ),
        migrations.RemoveField(
            model_name="page",
            name="support_copy_paste",
        ),
        migrations.AlterField(
            model_name="historicalpage",
            name="content",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historicalpage",
            name="content_cy",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historicalpage",
            name="content_de",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historicalpage",
            name="content_en",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historicalpage",
            name="content_en_us",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historicalpage",
            name="content_fr",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historicalpage",
            name="content_nl",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="content",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="content_cy",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="content_de",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="content_en",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="content_en_us",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="content_fr",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="content_nl",
            field=core.model_utils.JanewayBleachField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="submissionitem",
            name="text",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="submissionitem",
            name="text_cy",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="submissionitem",
            name="text_de",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="submissionitem",
            name="text_en",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="submissionitem",
            name="text_en_us",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="submissionitem",
            name="text_fr",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="submissionitem",
            name="text_nl",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
    ]

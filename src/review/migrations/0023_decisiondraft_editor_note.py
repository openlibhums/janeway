from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0022_remove_reviewform_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='decisiondraft',
            name='editor_note',
            field=models.TextField(blank=True, help_text='This note is shown to the author on the revision page, above the reviews, and is inserted into the decision email. Required when requesting revisions.', null=True, verbose_name='Note to Author'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussion', '0007_post_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='edited',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp of the last edit, if any.',
                null=True,
            ),
        ),
    ]

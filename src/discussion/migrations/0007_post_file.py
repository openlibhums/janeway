import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('discussion', '0006_post_is_system_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='file',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional file attachment.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='core.file',
            ),
        ),
    ]

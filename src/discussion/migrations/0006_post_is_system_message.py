from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussion', '0005_thread_participants_alter_post_thread_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_system_message',
            field=models.BooleanField(
                default=False,
                help_text='System-generated message, e.g. title change or participant added.',
            ),
        ),
    ]

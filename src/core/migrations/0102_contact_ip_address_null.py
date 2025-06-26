from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0101_delete_blank_keywords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='client_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]

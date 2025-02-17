from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0099_alter_accountrole_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='client_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]

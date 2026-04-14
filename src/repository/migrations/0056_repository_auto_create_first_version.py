from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("repository", "0055_alter_historicalrepository_comment_approved_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalrepository",
            name="auto_create_first_version",
            field=models.BooleanField(
                default=True,
                help_text="If enabled, the file uploaded during submission will automatically become the first version when the author completes their submission, so managers do not need to manually create one before accepting.",
                verbose_name="Auto-create first version on submission",
            ),
        ),
        migrations.AddField(
            model_name="repository",
            name="auto_create_first_version",
            field=models.BooleanField(
                default=True,
                help_text="If enabled, the file uploaded during submission will automatically become the first version when the author completes their submission, so managers do not need to manually create one before accepting.",
                verbose_name="Auto-create first version on submission",
            ),
        ),
    ]

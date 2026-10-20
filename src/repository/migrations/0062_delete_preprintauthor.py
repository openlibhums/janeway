from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0116_remove_controlledaffiliation_preprint_author"),
        ("repository", "0061_preprint_authors_to_frozen_authors"),
        ("submission", "0094_remove_creditrecord_preprint_author"),
    ]

    operations = [
        migrations.DeleteModel(
            name="PreprintAuthor",
        ),
    ]

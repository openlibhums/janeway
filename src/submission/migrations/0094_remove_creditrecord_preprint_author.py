from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("repository", "0061_preprint_authors_to_frozen_authors"),
        ("submission", "0093_frozenauthor_preprint"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="creditrecord",
            name="exclusive_fields_credit_record_frozen_author_preprint_author",
        ),
        migrations.RemoveField(
            model_name="creditrecord",
            name="preprint_author",
        ),
    ]

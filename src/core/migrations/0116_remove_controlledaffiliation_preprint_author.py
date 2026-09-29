from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0115_merge_20260710_1655"),
        ("repository", "0061_preprint_authors_to_frozen_authors"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="controlledaffiliation",
            name="exclusive_fields_controlled_affiliation_account_frozen_authoac77",
        ),
        migrations.RemoveField(
            model_name="controlledaffiliation",
            name="preprint_author",
        ),
        migrations.AddConstraint(
            model_name="controlledaffiliation",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("account__isnull", False), ("frozen_author__isnull", True)
                    ),
                    models.Q(
                        ("frozen_author__isnull", False), ("account__isnull", True)
                    ),
                    models.Q(
                        ("account__isnull", True), ("frozen_author__isnull", True)
                    ),
                    _connector="OR",
                ),
                name="exclusive_fields_controlled_affiliation_account_frozen_author",
            ),
        ),
    ]

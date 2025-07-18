# Generated by Django 4.2.21 on 2025-06-25 16:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0021_auto_20250625_1634"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="navigationitem",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("link__isnull", True), ("has_sub_nav", True)),
                    models.Q(("link__isnull", False), ("has_sub_nav", False)),
                    models.Q(("link__isnull", True), ("has_sub_nav", False)),
                    _connector="OR",
                ),
                name="nav_item_has_either_link_or_sub_nav",
                violation_error_message="There cannot be both a link and a sub navigation.",
            ),
        ),
    ]

from git import Repo
import json
import os

from django.conf import settings

from django.core.management.base import BaseCommand
from django.utils import timezone

from utils.logger import get_logger


logger = get_logger(__name__)


TEMPLATE = """
from django.db import migrations
from utils import migration_utils


SETTINGS_TO_UPDATE = REPLACE_SETTINGS_TO_UPDATE


def replace_values(apps, schema_editor):
    for key, values in SETTINGS_TO_UPDATE.items():
        group, name = key
        old_value = values["old_value"]
        new_value = values["new_value"]
        migration_utils.update_default_setting_values(
            apps,
            setting_name=name,
            group_name=group,
            values_to_replace=[old_value],
            replacement_value=new_value,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("???", "???"),
    ]

    operations = [
        migrations.RunPython(
            replace_values,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
"""


class Command(BaseCommand):
    """
    Makes a migration from Git history to update default setting values in the
    database.

    Example usage:
    python src/manage.py make_migration_for_setting_values 0044_update_settings_with_safe_title_html 0567134667789ba9d647bb3277b5afdd422cd834 b-5495-maths-titles-abstracts
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "migration_name",
            help="The filename that will be created in utils/migrations",
        )
        parser.add_argument(
            "from_ref",
            help="The commit hash or branch with the old setting values",
        )
        parser.add_argument(
            "to_ref",
            help="The commit hash or branch with the new setting values",
        )

    def read_settings_file(self, settings_to_update, record_as="old_value"):
        assert record_as in ["old_value", "new_value"]
        with open("src/utils/install/journal_defaults.json", "r") as fileref:
            settings = json.loads(fileref.read())
            for setting in settings:
                key = (setting["group"]["name"], setting["setting"]["name"])
                if record_as == "old_value":
                    settings_to_update[key] = {"old_value": setting["value"]["default"]}
                elif record_as == "new_value":
                    if (
                        settings_to_update[key]["old_value"]
                        == setting["value"]["default"]
                    ):
                        settings_to_update.pop(key)
                    else:
                        settings_to_update[key]["new_value"] = setting["value"][
                            "default"
                        ]
        return settings_to_update

    def checkout_both_versions(self, settings_to_update, from_ref, to_ref):
        repo = Repo(".")
        assert not repo.bare
        assert not repo.is_dirty()
        repo.git.checkout(from_ref)
        settings_to_update = self.read_settings_file(
            settings_to_update, record_as="old_value"
        )
        repo.git.checkout(to_ref)
        settings_to_update = self.read_settings_file(
            settings_to_update, record_as="new_value"
        )
        return settings_to_update

    def handle(self, *args, **options):
        settings_to_update = {}
        from_ref = options.get("from_ref")
        to_ref = options.get("to_ref")
        migration_name = options.get("migration_name")

        settings_to_update = self.checkout_both_versions(
            settings_to_update,
            from_ref,
            to_ref,
        )

        timestamp = timezone.datetime.now().strftime("%Y%m%d")
        migration_out_path = os.path.join(
            settings.BASE_DIR,
            "utils",
            "migrations",
            f"{migration_name}_{timestamp}.py",
        )
        migration = TEMPLATE.replace(
            "REPLACE_SETTINGS_TO_UPDATE", str(settings_to_update)
        )
        with open(migration_out_path, "w") as fileref:
            fileref.write(migration)

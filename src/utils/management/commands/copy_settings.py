from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from journal.models import Journal
from core.models import SettingValue
from cms.models import Page, SubmissionItem

IGNORED_SETTINGS = {"journal_name", "journal_issn", "print_issn"}


class Command(BaseCommand):
    help = "Copy settings, CMS pages, and submission items from one Janeway journal to another."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from",
            dest="from_journal",
            required=True,
            help="Journal code or ID of the journal to copy settings and pages from.",
        )
        parser.add_argument(
            "--to",
            dest="to_journal",
            required=True,
            help="Journal code or ID of the journal to copy settings and pages to.",
        )
        parser.add_argument(
            "--ignore-settings",
            action="store_true",
            help="If set, will ignore specific settings such as journal_name, journal_issn, and print_issn.",
        )

    def handle(self, *args, **options):
        from_journal_code_or_id = options["from_journal"]
        to_journal_code_or_id = options["to_journal"]
        ignore_settings = options["ignore_settings"]

        try:
            from_journal = Journal.objects.get(
                id=from_journal_code_or_id
            ) if from_journal_code_or_id.isdigit() else Journal.objects.get(
                code=from_journal_code_or_id
            )
        except Journal.DoesNotExist:
            raise CommandError(f"Journal '{from_journal_code_or_id}' not found.")

        try:
            to_journal = Journal.objects.get(
                id=to_journal_code_or_id
            ) if to_journal_code_or_id.isdigit() else Journal.objects.get(
                code=to_journal_code_or_id
            )
        except Journal.DoesNotExist:
            raise CommandError(f"Journal '{to_journal_code_or_id}' not found.")

        self.stdout.write(f"Copying settings from {from_journal} to {to_journal}...")

        existing_settings = SettingValue.objects.filter(journal=from_journal)

        for setting_value in existing_settings:
            if ignore_settings and setting_value.setting.name in IGNORED_SETTINGS:
                continue

            SettingValue.objects.update_or_create(
                journal=to_journal,
                setting=setting_value.setting,
                defaults={"value": setting_value.value},
            )

        self.stdout.write(self.style.SUCCESS("Settings copied successfully."))

        self.stdout.write(f"Copying CMS pages from {from_journal} to {to_journal}...")

        existing_pages = Page.objects.filter(object_id=from_journal.id,
                                             content_type=ContentType.objects.get_for_model(
                                                 Journal))

        for page in existing_pages:
            Page.objects.create(
                content_type=page.content_type,
                object_id=to_journal.id,
                name=page.name,
                display_name=page.display_name,
                template=page.template,
                content=page.content,
                is_markdown=page.is_markdown,
                edited=timezone.now(),
                display_toc=page.display_toc,
            )

        self.stdout.write(self.style.SUCCESS("CMS pages copied successfully."))

        self.stdout.write(
            f"Copying Submission Items from {from_journal} to {to_journal}...")

        existing_submission_items = SubmissionItem.objects.filter(journal=from_journal)

        for item in existing_submission_items:
            SubmissionItem.objects.update_or_create(
                journal=to_journal,
                existing_setting=item.existing_setting,
                defaults={
                    "title": item.title,
                    "text": item.text,
                    "order": item.order,
                },
            )

        self.stdout.write(self.style.SUCCESS("Submission Items copied successfully."))

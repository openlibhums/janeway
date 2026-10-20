from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from faker import Faker
from faker.providers import DynamicProvider
import secrets

from utils.logic import get_aware_datetime
from utils.logger import get_logger
from press import models as press_models
from journal import models as journal_models
from core import models as core_models
from utils.testing.helpers import create_news_item

fake = Faker()
logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Generates fake news items at the press and journal levels"

    press = press_models.Press.objects.first()
    press_content_type = ContentType.objects.get_for_model(press_models.Press)
    journals = journal_models.Journal.objects.all()
    journal_content_type = ContentType.objects.get_for_model(journal_models.Journal)

    @classmethod
    def build_fake_news_item(cls, content_type, obj_pk, posted_by):
        title = fake.sentence()
        body = ""
        for num in range(0, 10):
            body += f"<p>{fake.text()}</p>"
        date = get_aware_datetime(fake.date())
        tags = [fake.word() for i in range(0, 3)]
        create_news_item(
            content_type,
            obj_pk,
            title=title,
            body=body,
            posted=date,
            posted_by=posted_by,
            start_display=date,
            tags=tags,
        )

    def handle(self, *args, **options):
        confirmation = input(
            "News items will be public if this installation is live. Create fake items? (y/n)"
        )
        if confirmation.lower() != "y":
            return

        for each in range(0, 30):
            posted_by = core_models.Account.objects.filter(is_staff=True).first()
            if not posted_by:
                logger.warn("Staff member required")
                return
            self.build_fake_news_item(self.press_content_type, self.press.pk, posted_by)
        for journal in self.journals:
            for each in range(0, 30):
                posted_by = core_models.Account.objects.filter(
                    accountrole__role__slug="editor", accountrole__journal=journal
                ).first()
                if not posted_by:
                    logger.warn(f"Editor required for journal {journal}")
                    return
                self.build_fake_news_item(
                    self.journal_content_type, journal.pk, posted_by
                )
        logger.debug(self.style.SUCCESS("Successfully created news items"))

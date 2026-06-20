from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType


from journal import models as journal_models
from cms import models as cms_models
from utils.logger import get_logger
from utils.shared import clear_cache


logger = get_logger(__name__)


class Command(BaseCommand):
    """
    Puts the journal code on the beginning of paths created originally on
    domain mode sites.
    """

    def add_arguments(self, parser):
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        journals = journal_models.Journal.objects.all()
        for journal in journals:
            journal_type = ContentType.objects.get_for_model(journal)
            nav_items = cms_models.NavigationItem.objects.filter(
                object_id=journal.pk, content_type=journal_type
            )
            for nav_item in nav_items:
                if nav_item.link:
                    if (
                        not nav_item.link.startswith(journal.code)
                        and not nav_item.is_external
                    ):
                        slash = "/" if not nav_item.link.startswith("/") else ""
                        nav_item.link = f"{journal.code}{slash}{nav_item.link}"
                        nav_item.save()
        clear_cache()

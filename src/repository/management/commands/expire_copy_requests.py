from unittest.mock import Mock

from django.core.management.base import BaseCommand
from django.http import HttpRequest

from repository import copy_requests, models


class Command(BaseCommand):
    help = (
        "Expire requests for a copy that haven't been answered within {} days, "
        "and tell the readers. Run it daily from cron.".format(
            models.CopyRequest.ANSWER_DAYS
        )
    )

    def handle(self, *args, **options):
        request = Mock(HttpRequest)
        request.GET = Mock()
        request.user = None
        request.journal = None
        request.repository = None
        request.site_type = None
        request.FILES = None
        request.META = {}
        count = copy_requests.expire(request)
        self.stdout.write("{} request(s) expired.".format(count))

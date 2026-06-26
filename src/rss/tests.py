__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.test import TestCase, override_settings
from django.urls.base import clear_script_prefix
from django.utils import timezone

from repository import models as repository_models
from utils.testing import helpers


class TestFeedURLs(TestCase):
    """A catch-all pattern in rss/urls.py used to swallow un-slashed feed
    URLs such as /rss/preprints, serving the articles feed instead of
    letting APPEND_SLASH redirect to the correct feed.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.repo_manager = helpers.create_user("rss_manager@janeway.systems")
        cls.repository_domain = "rsstestrepo.domain.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.repository_domain,
        )
        cls.preprint_author = helpers.create_user("rss_author@janeway.systems")
        cls.preprint = helpers.create_preprint(
            cls.repository,
            cls.preprint_author,
            cls.subject,
            title="RSS Test Preprint",
        )
        cls.preprint.stage = repository_models.STAGE_PREPRINT_PUBLISHED
        cls.preprint.date_published = timezone.now()
        cls.preprint.save()

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_preprints_feed_without_trailing_slash_serves_preprint_data(self):
        response = self.client.get(
            "/rss/preprints",
            SERVER_NAME=self.repository_domain,
            follow=True,
        )
        self.assertRedirects(
            response,
            "/rss/preprints/",
            status_code=301,
        )
        self.assertIn(self.preprint.title, response.content.decode())

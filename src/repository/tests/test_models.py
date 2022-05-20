__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Andy Byers, Mauro Sanchez & Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.test import TestCase

from utils.testing import helpers
from core import models as cm
from submission import models as sm
from repository import models as rm


class TestModels(TestCase):
    def setUp(self):
        self.press = helpers.create_press()
        self.press.save()
        self.journal_one, self.journal_two = helpers.create_journals()
        self.request = helpers.Request()
        self.request.press = self.press
        self.request.journal = self.journal_one
        self.article_one = helpers.create_article(self.journal_one)
        self.repository = helpers.create_repository(self.press, [], [])

        self.section = sm.Section.objects.filter(
            journal=self.journal_one,
        ).first()

        self.subject = rm.Subject.objects.create(
            repository=self.repository,
            name='Test Subject',
            enabled=True,
        )
        self.preprint_author = helpers.create_user(
            username='repo_author@janeway.systems',
        )
        self.preprint_one = helpers.create_preprint(
            self.repository,
            self.preprint_author,
            self.subject,
            title='Preprint Number One',
        )
        self.preprint_two = helpers.create_preprint(
            self.repository,
            self.preprint_author,
            self.subject,
            title='Preprint Number Two',
        )

    def test_create_article(self):
        article = self.preprint_one.create_article(
            journal=self.journal_one,
            workflow_stage='Unassigned',
            journal_section=self.section,
        )

    def test_create_article_force(self):
        pass

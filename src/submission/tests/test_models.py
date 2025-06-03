__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.db import IntegrityError
from django.test import TestCase

from submission import models
from utils.testing import helpers


class FrozenAuthorModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)
        cls.frozen_author = models.FrozenAuthor.objects.create(
            article=cls.article_one,
            name_prefix='Dr.',
            first_name='S.',
            middle_name='Bella',
            last_name='Rogers',
            name_suffix='Esq.',
        )

    def test_full_name(self):
        self.assertEqual('Dr. S. Bella Rogers Esq.', self.frozen_author.full_name())

    def test_credits(self):
        self.frozen_author.add_credit('conceptualization')
        self.assertEqual(
            self.frozen_author.credits.first().get_role_display(),
            'Conceptualization',
        )


class CreditRecordTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)
        cls.frozen_author_one = helpers.create_frozen_author(cls.article_one)

    def test_article_authors_and_credits_for_frozen_author(self):
        role = self.frozen_author_one.add_credit('writing-original-draft')
        expected_frozen_authors = [
            fa for fa, _ in self.article_one.authors_and_credits().items()
        ]
        self.assertEqual(expected_frozen_authors, [self.frozen_author_one])
        expected_roles = [
            roles for _, roles in self.article_one.authors_and_credits().items()
        ]
        self.assertEqual(expected_roles[0].first(), role)

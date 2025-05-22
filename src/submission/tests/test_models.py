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
            self.frozen_author.credits().first().get_role_display(),
            'Conceptualization',
        )


class CreditRecordTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)
        cls.author_one = helpers.create_author(cls.journal_one)
        cls.article_one.authors.add(cls.author_one)
        cls.article_one.correspondence_author = cls.author_one
        cls.article_one.save()
        cls.frozen_author_one = models.FrozenAuthor.objects.create(
            author=cls.author_one,
            article=cls.article_one,
        )

    def test_credit_record_has_exclusive_fields_constraint(self):
        with self.assertRaises(IntegrityError):
            models.CreditRecord.objects.create(
                author=self.author_one,
                frozen_author=self.frozen_author_one,
                article=self.article_one,
                role='writing-original-draft',
            )

    def test_article_authors_and_credits_for_author(self):
        article = helpers.create_article(self.journal_one)
        author = helpers.create_author(self.journal_one)
        article.authors.add(author)
        role = author.add_credit('writing-original-draft', article=article)
        models.ArticleAuthorOrder.objects.get_or_create(
            article=article,
            author=author,
            defaults={'order': article.next_author_sort()},
        )
        expected_authors = [
            author for author, roles in article.authors_and_credits().items()
        ]
        self.assertEqual(expected_authors, [author])
        expected_roles = [
            roles for author, roles in article.authors_and_credits().items()
        ]
        self.assertEqual(expected_roles[0].first(), role)

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

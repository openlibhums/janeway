from unittest.mock import patch

from django.test import TestCase

from submission.models import FrozenAuthor
from utils.testing import helpers


class TestBackwardsCompatAuthorsSignal(TestCase):
    def setUp(self):
        self.journal, _ = helpers.create_journals()
        self.article = helpers.create_article(
            title="Test Article", journal=self.journal
        )
        self.account1 = helpers.create_user(
            "author_one@email.com", ["author"], self.journal
        )
        self.account2 = helpers.create_user(
            "author_two@email.com", ["author"], self.journal
        )

    def test_signal_creates_frozen_author_on_add(self):
        self.article.authors.add(self.account1)
        self.assertTrue(
            FrozenAuthor.objects.filter(
                article=self.article, author=self.account1
            ).exists()
        )

    def test_signal_removes_frozen_author_on_remove(self):
        frozen_author = FrozenAuthor.objects.create(
            article=self.article,
            author=self.account1,
        )
        self.article.authors.add(self.account1)
        self.article.authors.remove(self.account1)
        self.assertFalse(FrozenAuthor.objects.filter(pk=frozen_author.pk).exists())

    def test_signal_removes_all_frozen_authors_on_clear(self):
        FrozenAuthor.objects.create(article=self.article, author=self.account1)
        FrozenAuthor.objects.create(article=self.article, author=self.account2)
        self.article.authors.add(self.account1, self.account2)
        self.article.authors.clear()
        self.assertFalse(FrozenAuthor.objects.filter(article=self.article).exists())


class TestRemoveAuthorFromArticleSignal(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.journal, _ = helpers.create_journals()
        cls.article = helpers.create_article(title="Test Article", journal=cls.journal)
        cls.account1 = helpers.create_user(
            "author_one@email.com", ["author"], cls.journal
        )
        cls.author1 = helpers.create_frozen_author(cls.article, author=cls.account1)
        cls.account2 = helpers.create_user(
            "author_two@email.com", ["author"], cls.journal
        )
        cls.author2 = helpers.create_frozen_author(cls.article, author=cls.account2)
        cls.article.authors.add(cls.account1, cls.account2)

    def test_signal_removes_account_from_authors_m2m(self):
        self.author1.delete()
        self.assertEqual(
            [self.account2],
            [account for account in self.article.authors.all()],
        )

    @patch("submission.models.backwards_compat_authors")
    def test_signal_does_not_trigger_backwards_compat_if_no_m2m_authors(
        self, backwards_compat
    ):
        account3 = helpers.create_user(
            "author_three@email.com", ["author"], self.journal
        )
        author3 = helpers.create_frozen_author(self.article, author=account3)
        author3.delete()
        backwards_compat.assert_not_called()

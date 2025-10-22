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

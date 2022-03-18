from django.test import TestCase

from identifiers import logic, models
from utils.testing import helpers
from utils.shared import clear_cache


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.ten_articles = [helpers.create_article(cls.journal_one) for i in range(10)]
        cls.ten_identifiers = logic.get_doi_identifiers_for_articles(cls.ten_articles)


    def test_crossref_deposit(self):
        template = 'common/identifiers/crossref_doi_batch.xml'
        template_context = logic.create_crossref_doi_batch_context(
            self.journal_one,
            set(self.ten_identifiers)
        )
        deposit = logic.render_to_string(template, template_context)
        crd = models.CrossrefDeposit(
            [identifier.pk for identifier in self.ten_identifiers],
            deposit=deposit,
        )
        pass

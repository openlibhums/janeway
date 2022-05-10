from django.test import TestCase

from identifiers import logic, models
from utils.testing import helpers
from utils.shared import clear_cache
from uuid import uuid4


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        from utils.setting_handler import save_setting
        save_setting('general', 'journal_issn', cls.journal_one, '1234-5678')
        save_setting('general', 'print_issn', cls.journal_one, '8765-4321')
        save_setting('Identifiers', 'use_crossref', cls.journal_one, True)
        save_setting('Identifiers', 'crossref_prefix', cls.journal_one, '10.0000')
        cls.ten_articles = [helpers.create_article(cls.journal_one) for i in range(10)]
        cls.ten_identifiers = logic.get_dois_for_articles(cls.ten_articles, create=True)


    def test_crossref_deposit(self):
        template = 'common/identifiers/crossref_doi_batch.xml'
        template_context = logic.create_crossref_doi_batch_context(
            self.journal_one,
            set(self.ten_identifiers)
        )
        deposit = logic.render_to_string(template, template_context)
        filename = uuid4()
        crd = models.CrossrefDeposit.objects.create(deposit=deposit, file_name=filename)
        crd.identifiers.add(*self.ten_identifiers)
        crd.save()
        self.assertTrue('10.0000/TST.9' in str(crd))

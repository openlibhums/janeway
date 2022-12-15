from django.test import TestCase
from django.shortcuts import reverse
from django.urls.base import clear_script_prefix

from production.logic import remove_css_from_html
from production import models
from utils.testing import helpers
from submission import models as submission_models


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        clear_script_prefix()
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            'typesetter@janeway.systems',
            roles=['editor'],
            journal=cls.journal_one,
            atrrs={'is_active': True,}
        )
        cls.typesetter = helpers.create_user(
            'typesetter@janeway.systems',
            roles=['typesetter'],
            journal=cls.journal_one,
        )
        cls.typesetter.is_active = True
        cls.typesetter.save()
        cls.active_article = helpers.create_article(
            journal=cls.journal_one,
        )
        cls.archived_article = helpers.create_article(
            journal=cls.journal_one,
        )
        cls.archived_article.stage = submission_models.STAGE_ARCHIVED
        cls.archived_article.save()
        cls.active_production_assignment = models.ProductionAssignment.objects.create(
            article=cls.active_article,
            production_manager=cls.editor,
            editor=cls.editor,
        )
        cls.active_typesetting_task = models.TypesetTask.objects.create(
            assignment=cls.active_production_assignment,
            typesetter=cls.typesetter,
            typeset_task='Active Task',
        )
        cls.archived_production_assignment = models.ProductionAssignment.objects.create(
            article=cls.archived_article,
            production_manager=cls.editor,
            editor=cls.editor,
        )
        cls.archived_typesetting_task = models.TypesetTask.objects.create(
            assignment=cls.active_production_assignment,
            typesetter=cls.typesetter,
            typeset_task='Archive Task',
        )

    def test_remove_css_from_html(self):
        test_html = """
            <html>
              <head>
                <link rel="stylesheet" type="text/css" href="mystyle.css">
              </head>
              <body>
                <style>
                  .banana{"width": 100}
                </style>
                <p style="color:red;">This is a paragraph.</p>
              </body>
            </html>
        """
        expected_html = '<html>\n <head>\n </head>\n <body>\n  <p>\n   This is a paragraph.\n  </p>\n </body>\n</html>\n'

        result = remove_css_from_html(test_html)
        self.assertMultiLineEqual(result, expected_html)

    def test_archive_stage_hides_task(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(
            reverse('typesetter_requests')
        )
        self.assertContains(
            response,
            'Active Task',
        )
        self.assertNotContains(
            response,
            'Archived Task'
        )

    def test_archived_article_task_404s(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(
            reverse(
                'do_typeset_task',
                kwargs={
                    'typeset_id': self.archived_typesetting_task.pk
                }
            )
        )
        self.assertTrue(
            response.status_code,
            404,
        )

    def test_active_article_task_200s(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(
            reverse(
                'do_typeset_task',
                kwargs={
                    'typeset_id': self.archived_typesetting_task.pk
                }
            )
        )
        self.assertTrue(
            response.status_code,
            200,
        )



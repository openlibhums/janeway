from django.test import TestCase, override_settings
from django.shortcuts import reverse
from utils.testing import helpers


class TestOverview(TestCase):

	def setUp(self):
		self.press = helpers.create_press()
		self.journal_one, self.journal_two = helpers.create_journals()
		self.editor = helpers.create_editor(self.journal_one)
		self.unassigned_article = helpers.create_article(journal=self.journal_one)


	@override_settings(URL_CONFIG='domain')
	def test_editor_can_access_workflow_overview(self):
		self.client.force_login(self.editor)
		url = reverse(
			'workflow_overview',
		)
		response = self.client.get(url, SERVER_NAME='testserver')
		self.assertEqual(response.status_code, 200)


	@override_settings
	def test_article_renders_with_article(self):
		self.client.force_login(self.editor)
		url = reverse(
			'workflow_overview',
		)
		response = self.client.get(url, SERVER_NAME='testserver')
		self.assertContains(
			response, self.unassigned_article.title,
		)


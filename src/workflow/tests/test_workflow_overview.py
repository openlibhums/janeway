from django.core.management import call_command

from utils.testing import helpers


class TestOverview(TestCase):

	def setUp(self):
		self.press = helpers.create_press()
		self.journal_one, self.journal_two = helpers.create_journals
		self.editor = helpers.create_user(
			username='editor@janeway.systems',
			roles=['editor'],
			journal=self.journal_one,
		)
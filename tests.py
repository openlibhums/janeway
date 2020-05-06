__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from plugins.typesetting import plugin_settings
from utils.testing import helpers


class TestTypesetting(TestCase):
    # Tests for editor role checks

    @classmethod
    def setUpTestData(self):
        """
        Setup the test environment.
        :return: None
        """
        roles_to_setup = [
            "editor",
            "production",
        ]

        self.journal_one, self.journal_two = helpers.create_journals()
        helpers.create_roles(roles_to_setup)

        self.article_owner = helpers.create_regular_user()

        self.private_file = core_models.File.objects.create(
            mime_type="A/FILE",
            original_filename="blah.txt",
            uuid_filename="UUID.txt",
            label="A file that is private",
            description="Oh yes, it's a file",
            owner=self.regular_user,
            is_galley=False,
            privacy="owner",
        )

        self.article_in_typesetting = submission_models.Article.create(
        	owner=self.regular_user, 
        	title="A Test Article",
			abstract="An abstract",
			stage=plugin_settings.STAGE,
			journal_id=self.journal_one.id
        )

from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from core import models as core_models, files
from utils.testing import helpers


class GalleyViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create press, journals and an editor
        helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            'emh@voyager.com',
            ['editor'],
            cls.journal_one,
        )

        # Create test files
        cls.file_with_unsupported_mime = core_models.File.objects.create(
            mime_type='unsupported/type',
            original_filename='unsupported_file.txt',
            uuid_filename='unsupported_file_uuid.txt'
        )

        cls.file_with_supported_mime = core_models.File.objects.create(
            mime_type=files.MIMETYPES_WITH_FIGURES[0],
            original_filename='supported_file.txt',
            uuid_filename='supported_file_uuid.txt'
        )

        # Create test articles
        cls.article = helpers.create_article(
            cls.journal_one,
        )
        # Create galleys
        cls.galley_with_unsupported_file = core_models.Galley.objects.create(
            article=cls.article,
            file=cls.file_with_unsupported_mime
        )

        cls.galley_without_file = core_models.Galley.objects.create(
            article=cls.article,
            file=None
        )

        cls.galley_with_supported_file = core_models.Galley.objects.create(
            article=cls.article,
            file=cls.file_with_supported_mime
        )

    def setUp(self):
        self.client.force_login(self.editor)

    def test_galley_file_not_editable(self):
        response = self.client.get(reverse('edit_galley_file', kwargs={
            'article_id': self.article.id,
            'galley_id': self.galley_with_unsupported_file.id
        }))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertRedirects(response, reverse('editor_galley_list'))

    def test_galley_has_no_file(self):
        response = self.client.get(reverse('edit_galley_file', kwargs={
            'article_id': self.article.id,
            'galley_id': self.galley_without_file.id
        }))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertRedirects(response, reverse('editor_galley_list'))

    def test_galley_with_editable_file(self):
        response = self.client.get(reverse('edit_galley_file', kwargs={
            'article_id': self.article.id,
            'galley_id': self.galley_with_supported_file.id
        }))
        self.assertEqual(response.status_code, 200)

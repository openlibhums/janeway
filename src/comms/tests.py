from django.test import TestCase
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.files.base import ContentFile

from core import models as core_models
from comms import models
from utils.testing import helpers


class NewsViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.content_type = ContentType.objects.get_for_model(cls.journal_one)

        cls.editor = helpers.create_editor(cls.journal_one)
        cls.author = helpers.create_author(cls.journal_one)

        cls.news_item = models.NewsItem.objects.create(
            content_type=cls.content_type,
            object_id=cls.journal_one.pk,
            posted_by=cls.editor,
            title="Test News",
            body="Some content",  # Corrected from 'content' to 'body'
        )

        cls.news_url = reverse("core_manager_news")
        cls.manage_url = reverse(
            "core_manager_edit_news",
            kwargs={"news_pk": cls.news_item.pk},
        )
        cls.create_url = reverse("core_manager_create_news")

    def setUp(self):
        self.client.force_login(self.editor)

    def test_news_view_get(self):
        """Test that the news listing view renders correctly with existing items."""
        response = self.client.get(self.news_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test News")

    def test_news_delete_post(self):
        """Test that a POST with 'delete' removes the correct news item."""
        response = self.client.post(
            self.news_url,
            data={"delete": self.news_item.pk},
        )
        self.assertRedirects(response, self.news_url)
        self.assertFalse(models.NewsItem.objects.filter(pk=self.news_item.pk).exists())

    def test_manage_news_view_edit_get(self):
        """Test that the manage_news view loads for editing an existing item."""
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test News")

    def test_manage_news_view_create_post(self):
        """Test that posting new data to manage_news creates a new news item."""
        data = {
            "title": "New Item",
            "body": "This is new content.",
            "start_display": timezone.now().date(),
            "sequence": 1,
        }
        response = self.client.post(self.create_url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(models.NewsItem.objects.filter(title="New Item").exists())

    def test_manage_news_upload_image(self):
        """Test that an image file can be uploaded and linked to a news item."""
        image_data = ContentFile(b"fake image content", name="test.png")
        data = {
            "title": "Image News",
            "body": "With image",
            "start_display": timezone.now().date(),
            "sequence": 2,
            "image_file": image_data,
        }
        response = self.client.post(
            self.create_url,
            data=data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(models.NewsItem.objects.filter(title="Image News").exists())
        item = models.NewsItem.objects.get(title="Image News")
        self.assertIsNotNone(item.large_image_file)

    def test_manage_news_delete_image(self):
        """Test that an existing image file attached to a news item can be deleted."""
        image_file = core_models.File.objects.create(
            article_id=1,
            mime_type="image/png",
            original_filename="sample.png",
            uuid_filename="sample.png",
            owner=self.editor,
        )
        self.news_item.large_image_file = image_file
        self.news_item.save()

        response = self.client.post(
            self.manage_url,
            data={"delete_image": image_file.pk},
            follow=False,
        )

        self.assertTrue(
            response.url.startswith(self.manage_url),
            msg=f"Redirect URL was {response.url}, expected to start with {self.manage_url}",
        )

        self.assertFalse(
            core_models.File.objects.filter(pk=image_file.pk).exists(),
            msg="File was not deleted as expected.",
        )

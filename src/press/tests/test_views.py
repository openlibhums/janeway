__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.test import TestCase, override_settings

from core import models as core_models
from utils.testing import helpers


class PressViewTestsWithData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.press_manager = helpers.create_user(
            username="rcuaekqhrswerhrttydo@example.org",
        )
        cls.press_manager.is_active = True
        cls.press_manager.is_staff = True
        cls.press_manager.save()
        cls.contact_person = helpers.create_contact_person(
            cls.press_manager,
            cls.press,
        )
        cls.press_content_type = ContentType.objects.get_for_model(cls.press)


class URLWithReturnTests(PressViewTestsWithData):
    @override_settings(URL_CONFIG="domain")
    def test_press_nav_account_links_do_not_have_return(self):
        """
        Check that the url_with_return tag has *not* been used
        in the site nav links for login and registration.
        """
        response = self.client.get(
            "/",
            SERVER_NAME=self.press.domain,
        )
        content = response.content.decode()
        self.assertNotIn("/login/?next=", content)
        self.assertNotIn("/register/step/1/?next=", content)


class PressContactTests(PressViewTestsWithData):
    @override_settings(URL_CONFIG="domain")
    def test_press_contact_GET(self):
        response = self.client.get(
            reverse("press_contact"),
            SERVER_NAME=self.press.domain,
        )
        self.assertEqual(
            self.contact_person.account.email,
            response.context["contacts"][0].account.email,
        )
        self.assertEqual(
            [(self.press_manager.pk, self.press_manager.full_name())],
            response.context["contact_form"].fields["account"].choices,
        )
        self.assertTemplateUsed("press/journal/contact.html")

    @override_settings(URL_CONFIG="domain")
    def test_journal_contact_view_redirects_to_press_contact_when_no_journal(self):
        """
        The tested behavior is for backwards compatibility,
        since the press used to use the journal 'contact' view.
        """
        response = self.client.get(
            reverse("contact"),
            SERVER_NAME=self.press.domain,
            follow=True,
        )
        self.assertIn((reverse("press_contact"), 302), response.redirect_chain)

    @override_settings(URL_CONFIG="domain")
    @override_settings(CAPTCHA_TYPE="")
    def test_press_contact_POST(self):
        post_data = {
            "account": self.press_manager.pk,
            "sender": "notloggedin@example.org",
            "subject": "Idea for a publishing platform",
            "body": "There is a technology called paper, which...",
        }
        self.client.post(
            reverse("press_contact"),
            post_data,
            SERVER_NAME=self.press.domain,
        )
        self.assertTrue(
            core_models.ContactMessage.objects.filter(
                sender="notloggedin@example.org",
                content_type=self.press_content_type,
                object_id=self.press.pk,
            ).exists(),
        )

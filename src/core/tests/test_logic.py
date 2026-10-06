__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import uuid
from mock import patch

from django.shortcuts import reverse
from django.test import TestCase, override_settings

from core import logic, models
from utils.testing import helpers


class TestLogic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.request = helpers.get_request(
            press=cls.press,
            journal=cls.journal_one,
        )
        cls.inactive_user = helpers.create_user("zlwdi6frbtlh4gditdir@example.org")
        cls.inactive_user.is_active = False
        cls.inactive_user.confirmation_code = "8bd3cdc9-1c3c-4ec9-99bc-9ea0b86a3c55"
        cls.inactive_user.clean()
        cls.inactive_user.save()

        # A decoded next URL
        cls.next_url_raw = "/target/page/?q=a"

        # An encoded next URL
        cls.next_url_encoded = "/target/page/%3Fq%3Da"

    def test_render_nested_settings(self):
        expected_rendered_setting = '<p>For help with Janeway, contact <a href="mailto:--No support email set--">--No support email set--</a>.</p>'
        rendered_setting = logic.render_nested_setting(
            "support_contact_message_for_staff",
            "general",
            self.request,
            nested_settings=[("support_email", "general")],
        )
        self.assertEqual(expected_rendered_setting, rendered_setting)

    @patch("core.logic.reverse")
    def test_reverse_with_next_in_kwarg(self, mock_reverse):
        mock_reverse.return_value = "/my/path/?my=params"
        reversed_url = logic.reverse_with_next(
            "/test/",
            next_url=self.next_url_raw,
        )
        self.assertIn(self.next_url_encoded, reversed_url)

    @patch("core.logic.reverse")
    def test_reverse_with_next_no_next(self, mock_reverse):
        mock_reverse.return_value = "/my/url/?my=params"
        reversed_url = logic.reverse_with_next("/test/", "")
        self.assertEqual(mock_reverse.return_value, reversed_url)

    @patch("core.logic.reverse")
    def test_reverse_with_query(self, mock_reverse):
        mock_reverse.return_value = "/my/url/?my=params"
        reversed_url = logic.reverse_with_query(
            "/test/",
            query_params={
                "important": "stuff",
            },
        )
        self.assertIn("important=stuff", reversed_url)

    def test_get_confirm_account_url(self):
        url = logic.get_confirm_account_url(
            self.request,
            self.inactive_user,
            next_url=self.next_url_raw,
        )
        self.assertIn(
            f"/register/step/2/8bd3cdc9-1c3c-4ec9-99bc-9ea0b86a3c55/?next={self.next_url_encoded}",
            url,
        )


class TestSearchOrganizations(TestCase):
    @staticmethod
    def make_organization(ror_id, display, aliases=(), acronyms=(), labels=()):
        organization = models.Organization.objects.create(ror_id=ror_id)
        models.OrganizationName.objects.create(
            value=display, ror_display_for=organization
        )
        for alias in aliases:
            models.OrganizationName.objects.create(value=alias, alias_for=organization)
        for acronym in acronyms:
            models.OrganizationName.objects.create(
                value=acronym, acronym_for=organization
            )
        for label in labels:
            models.OrganizationName.objects.create(value=label, label_for=organization)
        return organization

    @classmethod
    def setUpTestData(cls):
        cls.oxford = cls.make_organization(
            "052gg0110",
            "University of Oxford",
            aliases=["Oxford", "Oxford University"],
            acronyms=["OU"],
        )
        cls.brookes = cls.make_organization(
            "04v2twj65", "Oxford Brookes University", acronyms=["OBU"]
        )
        cls.zeta = cls.make_organization(
            "00bbbbbbb", "Zeta Institute", aliases=["Old Oxford Hall"]
        )
        cls.alpha = cls.make_organization(
            "00ccccccc", "Alpha Institute", aliases=["Oxford Alpha"]
        )
        cls.bath = cls.make_organization("002h8g185", "Bath University")
        cls.aberdeen = cls.make_organization("016476m91", "Aberdeen University")
        cls.custom = models.Organization.objects.create()
        models.OrganizationName.objects.create(
            value="Oxford Custom", custom_label_for=cls.custom
        )

    def search(self, term):
        return list(logic.search_organizations(term, exclude_custom_labels=True)[:25])

    def test_each_organization_appears_once(self):
        # University of Oxford matches on several aliases
        self.assertEqual(
            self.search("Oxford"),
            [self.oxford, self.brookes, self.alpha, self.zeta],
        )

    def test_ties_are_alphabetical(self):
        self.assertEqual(
            self.search("university"),
            [self.oxford, self.aberdeen, self.bath, self.brookes],
        )

    def test_exact_acronym_ranks_first(self):
        self.assertEqual(self.search("OU")[0], self.oxford)

    def test_ror_id_match(self):
        self.assertEqual(self.search("052gg0110"), [self.oxford])

    def test_custom_labels_can_be_excluded(self):
        self.assertNotIn(self.custom, self.search("Oxford"))
        self.assertIn(
            self.custom, list(logic.search_organizations("Oxford Custom")[:25])
        )

    def test_count(self):
        results = logic.search_organizations("Oxford", exclude_custom_labels=True)
        self.assertEqual(results.count(), 4)
        self.assertEqual(len(results), 4)

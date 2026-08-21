__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from core import models as core_models, forms as core_forms
from utils import orcid
from utils.testing import helpers


class CoreFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(["author", "editor", "reviewer"])
        cls.user_email = "qoeyl8xibelnmpnbv9xv@example.org"
        cls.user_password = "uui6xss390977tedm7cd"
        cls.user = core_models.Account.objects.create_user(
            cls.user_email,
            password=cls.user_password,
        )
        cls.organization_bbk = core_models.Organization.objects.create(
            ror_id="02mb95055",
        )
        cls.name_bbk_uol = core_models.OrganizationName.objects.create(
            value="Birkbeck, University of London",
            language="en",
            ror_display_for=cls.organization_bbk,
            label_for=cls.organization_bbk,
        )
        cls.affiliation = core_models.ControlledAffiliation.objects.create(
            account=cls.user,
            organization=cls.organization_bbk,
        )

    def test_account_affiliation_form_clean_checks_duplicates(self):
        post_kwargs = {
            "title": "Professor",
            "department": "English",
            "is_primary": True,
        }
        form = core_forms.AccountAffiliationForm(
            post_kwargs,
            account=self.user,
            organization=self.organization_bbk,
        )
        if form.is_valid():
            form.save()

        # Re-create with duplicate data
        duplicate = core_forms.AccountAffiliationForm(
            post_kwargs,
            account=self.user,
            organization=self.organization_bbk,
        )
        is_valid = duplicate.is_valid()
        self.assertFalse(is_valid)

    @patch("utils.orcid.get_orcid_record")
    def test_orcid_affiliation_form_tzinfo(self, get_orcid_record):
        get_orcid_record.return_value = helpers.get_orcid_record_all_fields()
        core_models.Organization.objects.create(ror_id="03yrm5c26")
        orcid_details = orcid.get_orcid_record_details("test")
        orcid_affils = orcid_details.get("affiliations", [])

        form = core_forms.OrcidAffiliationForm(
            orcid_affiliation=orcid_affils[0],
            # Pass a raw string rather than a tzinfo subclass
            tzinfo="Europe/London",
            data={"account": self.user},
            journal=self.journal_one,
        )
        self.assertTrue(form.is_valid())

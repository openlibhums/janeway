__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from mock import patch
from types import SimpleNamespace
from uuid import uuid4
from django.core.cache import cache as django_cache
from django.test.client import RequestFactory
from django.urls.base import clear_script_prefix
from django.shortcuts import reverse
from django.test import Client, TestCase, override_settings
from django.template.loader import get_template
from django.utils import timezone

from core import models as core_models
from core import middleware as core_middleware
from core import views as core_views
from utils import orcid, setting_handler
from utils.template_override_middleware import Loader
from utils.testing import helpers


class CoreViewTestsWithData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(["author", "editor", "reviewer"])
        cls.themes = ["clean", "OLH", "material"]
        cls.user_email = "sukv8golcvwervs0y7e5@example.org"
        cls.user_password = "xUMXW1oXn2l8L26Kixi2"
        cls.user = core_models.Account.objects.create_user(
            cls.user_email,
            password=cls.user_password,
        )
        cls.user.confirmation_code = uuid4()
        cls.user.is_active = True
        cls.user_orcid = "0000-0001-2345-6789"
        cls.user_orcid_uri = f"https://orcid.org/{cls.user_orcid}/"
        cls.user.orcid = cls.user_orcid_uri
        cls.orcid_token_uuid = uuid4()
        cls.orcid_token = core_models.OrcidToken.objects.create(
            token=cls.orcid_token_uuid,
            orcid=cls.user_orcid_uri,
        )
        cls.reset_token_uuid = uuid4()
        cls.reset_token = core_models.PasswordResetToken.objects.create(
            account=cls.user,
            token=cls.reset_token_uuid,
        )
        cls.user.save()

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
        cls.country_us, _ = core_models.Country.objects.get_or_create(
            code="US",
            defaults={"name": "United States"},
        )
        cls.location_oakland = core_models.Location.objects.create(
            name="Oakland",
            geonames_id=5378538,
            country=cls.country_us,
        )
        cls.organization_cdl = core_models.Organization.objects.create(
            ror_id="03yrm5c26",
        )
        cls.organization_cdl.locations.add(cls.location_oakland)
        cls.name_cdl = core_models.OrganizationName.objects.create(
            value="California Digital Library",
            language="en",
            ror_display_for=cls.organization_cdl,
            label_for=cls.organization_cdl,
        )

        # The raw unicode string of a 'next' URL
        cls.next_url_raw = "/target/page/?a=b&x=y"

        # The unicode string url-encoded with safe='/'
        cls.next_url_encoded = "/target/page/%3Fa%3Db%26x%3Dy"

        # The unicode string url-encoded with safe='/' two times
        cls.next_url_doubly_encoded = "/target/page/%253Fa%253Db%2526x%253Dy"

        # The state parameter with action=login
        cls.state_login = orcid.encode_state(cls.next_url_raw, "login")

        # The state parameter including login and the next URL
        cls.state_register = orcid.encode_state(cls.next_url_raw, "register")

        # next_url_encoded with its 'next' key
        cls.next_url_query_string = "next=/target/page/%3Fa%3Db%26x%3Dy"

        # The core_login url with encoded next url
        cls.core_login_with_next = "/login/?next=/target/page/%3Fa%3Db%26x%3Dy"

    def setUp(self):
        clear_script_prefix()
        self.client = Client()


class AccountManagementTemplateTests(CoreViewTestsWithData):
    def test_user_login(self):
        url = "/login/"
        data = {}
        template = "admin/core/accounts/login.html"
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_get_reset_token(self):
        url = "/reset/step/1/"
        data = {}
        template = "admin/core/accounts/get_reset_token.html"
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_reset_password(self):
        url = f"/reset/step/2/{self.reset_token_uuid}/"
        data = {}
        template = "admin/core/accounts/reset_password.html"
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_register(self):
        url = "/register/step/1/"
        data = {}
        template = "admin/core/accounts/register.html"
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_orcid_registration(self):
        url = f"/register/step/orcid/{self.orcid_token_uuid}/"
        data = {}
        template = "admin/core/accounts/orcid_registration.html"
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_activate_account(self):
        url = f"/register/step/2/{self.user.confirmation_code}/"
        data = {}
        template = "admin/core/accounts/activate_account.html"
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_edit_profile(self):
        self.client.login(username=self.user_email, password=self.user_password)
        url = "/profile/"
        data = {}
        template = "admin/core/accounts/edit_profile.html"
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)


class GenericFacetedListViewTests(CoreViewTestsWithData):
    """
    A test suite for the core logic in GenericFacetedListView.
    Uses JournalUsers and BaseUserList to get access to URLs and facets
    as they are actually used, and so to help these tests catch
    potential regressions.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Journal 1 users
        cls.journal_one_authors = []
        for num in range(0, 30):
            cls.journal_one_authors.append(
                helpers.create_user(
                    f"author_{num}_eblazi52pnxnivl4vox2@example.org",
                    roles=["author"],
                    journal=cls.journal_one,
                )
            )
        cls.journal_one_editor = helpers.create_user(
            "editor_q2flnkp5ryxqtr5iuvvl@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.journal_one_editor.is_active = True
        cls.journal_one_editor.save()
        cls.journal_one_reviewer = cls.journal_one_authors[0]
        cls.journal_one_reviewer.add_account_role("reviewer", cls.journal_one)

        # Journal 2 users
        cls.journal_two_authors = []
        # The first five authors are the same as journal 1
        for author in cls.journal_one_authors[:5]:
            author.add_account_role("author", cls.journal_two)
            cls.journal_two_authors.append(author)

        # The next five are new
        for num in range(0, 5):
            cls.journal_two_authors.append(
                helpers.create_user(
                    f"author_{num}_c9zn2ag7efuyecanpyl1@example.org",
                    roles=["author"],
                    journal=cls.journal_two,
                )
            )
        # Journal 2's reviewer is the same as journal 1's 15th author
        cls.journal_two_reviewer = cls.journal_one_authors[15]
        cls.journal_two_reviewer.add_account_role(
            "reviewer",
            journal=cls.journal_two,
        )

    def setUp(self):
        super().setUp()
        self.client.force_login(self.journal_one_editor)

    def test_get_paginate_by_default(self):
        url = "/user/all/"
        data = {}
        response = self.client.get(url, data)
        self.assertEqual(response.context["paginate_by"], 25)
        self.assertEqual(len(response.context["account_list"]), 25)

    def test_get_paginate_by_all(self):
        url = "/user/all/"
        data = {
            "paginate_by": "all",
        }
        response = self.client.get(url, data)
        self.assertGreater(len(response.context["account_list"]), 25)

    def test_get_facet_form_foreign_key(self):
        """
        Checks that only account roles in Journal One
        are included in facet counts.
        """
        url = "/user/all/"
        data = {}
        response = self.client.get(url, data)
        form = response.context["facet_form"]
        labels = [label for pk, label in form.fields["accountrole__role__pk"].choices]
        self.assertEqual(labels, ["Author (30)", "Editor (1)", "Reviewer (1)"])

    def test_get_queryset_foreign_key(self):
        """
        Checks that only account roles in Journal One
        are included in queryset results.
        """
        url = "/user/all/"
        reviewer_role = core_models.Role.objects.get(slug="reviewer")
        data = {
            "accountrole__role__pk": reviewer_role.pk,
        }
        response = self.client.get(url, data)
        self.assertEqual(len(response.context["account_list"]), 1)


class UserLoginTests(CoreViewTestsWithData):
    @override_settings(URL_CONFIG="domain")
    def test_is_authenticated_redirects_to_next(self):
        self.client.login(username=self.user_email, password=self.user_password)
        get_data = {
            "next": self.next_url_raw,
        }
        url = f"/login/?next={self.next_url_encoded}"
        response = self.client.get(
            url,
            get_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @override_settings(URL_CONFIG="domain")
    @patch("core.views.authenticate")
    def test_login_success_redirects_to_next(self, authenticate):
        authenticate.return_value = self.user
        post_data = {
            "user_name": self.user_email,
            "user_pass": self.user_password,
        }
        url = f"/login/?next={self.next_url_encoded}"
        response = self.client.post(url, post_data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_OIDC=True)
    def test_oidc_link_has_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/login/",
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            f"/oidc/authenticate/?next={self.next_url_encoded}",
            response.content.decode(),
        )

    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_ORCID=True)
    def test_orcid_link_has_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/login/",
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            f"/login/orcid/?next={self.next_url_encoded}",
            response.content.decode(),
        )

    @override_settings(URL_CONFIG="domain")
    def test_forgot_password_link_has_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/login/",
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            f"/reset/step/1/?next={self.next_url_encoded}",
            response.content.decode(),
        )

    @override_settings(URL_CONFIG="domain")
    def test_register_link_has_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/login/",
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            f"/register/step/1/?next={self.next_url_encoded}",
            response.content.decode(),
        )


class UserLoginOrcidTests(CoreViewTestsWithData):
    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_ORCID=False)
    def test_orcid_disabled_redirects_with_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/login/orcid/",
            get_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(self.next_url_encoded, response.redirect_chain[0][0])

    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_ORCID=True)
    def test_no_orcid_code_redirects_with_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/login/orcid/",
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(self.next_url_doubly_encoded, response.url)

    @patch("core.views.orcid.retrieve_tokens")
    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_ORCID=True)
    def test_no_orcid_id_redirects_with_next(self, retrieve_tokens):
        retrieve_tokens.return_value = None
        get_data = {
            "code": "12345",
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/login/orcid/",
            get_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)

    @patch("core.views.orcid.retrieve_tokens")
    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_ORCID=True)
    def test_action_login_account_found_redirects_to_next(
        self,
        retrieve_tokens,
    ):
        retrieve_tokens.return_value = self.user_orcid_uri
        get_data = {
            "code": "12345",
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/login/orcid/",
            get_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch("core.views.orcid.get_orcid_record_details")
    @patch("core.views.orcid.retrieve_tokens")
    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_ORCID=True)
    def test_action_login_matching_email_redirects_to_next(
        self,
        retrieve_tokens,
        orcid_details,
    ):
        # Change ORCID so it doesn't work
        retrieve_tokens.return_value = "https://orcid.org/0000-0001-2312-3123"

        # Return an email that will work
        orcid_details.return_value = {"emails": [self.user_email]}

        get_data = {
            "code": "12345",
            "state": self.state_login,
        }
        response = self.client.get(
            "/login/orcid/",
            get_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch("core.views.orcid.get_orcid_record_details")
    @patch("core.views.orcid.retrieve_tokens")
    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_ORCID=True)
    def test_action_login_failure_redirects_with_next(
        self,
        retrieve_tokens,
        orcid_details,
    ):
        # Change ORCID so it doesn't work
        retrieve_tokens.return_value = "https://orcid.org/0000-0001-2312-3123"

        orcid_details.return_value = {"emails": []}
        get_data = {
            "code": "12345",
            "state": self.state_login,
        }
        response = self.client.get(
            "/login/orcid/",
            get_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            self.next_url_query_string,
            response.redirect_chain[0][0],
        )

    @patch("core.views.orcid.retrieve_tokens")
    @override_settings(URL_CONFIG="domain")
    @override_settings(ENABLE_ORCID=True)
    def test_action_register_redirects_with_next(self, retrieve_tokens):
        retrieve_tokens.return_value = self.user_orcid_uri
        get_data = {
            "code": "12345",
            "next": self.next_url_raw,
            "action": "register",
        }
        response = self.client.get(
            "/login/orcid/",
            get_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            self.next_url_query_string,
            response.redirect_chain[0][0],
        )


class GetResetTokenTests(CoreViewTestsWithData):
    @patch("core.views.logic.start_reset_process")
    @override_settings(URL_CONFIG="domain")
    def test_start_reset_redirects_with_next(self, _start_reset):
        post_data = {
            "email_address": self.user_email,
        }
        response = self.client.post(
            f"/reset/step/1/?next={self.next_url_encoded}",
            post_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)


class ResetPasswordTests(CoreViewTestsWithData):
    @patch("core.views.logic.password_policy_check")
    @override_settings(URL_CONFIG="domain")
    def test_reset_password_form_valid_redirects_with_next(self, password_check):
        password_check.return_value = None
        post_data = {
            "password_1": "qsX1roLama3ADotEopfq",
            "password_2": "qsX1roLama3ADotEopfq",
        }
        path = f"/reset/step/2/{self.reset_token.token}/"
        query = f"next={self.next_url_encoded}"
        response = self.client.post(
            f"{path}?{query}",
            post_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)


class RegisterTests(CoreViewTestsWithData):
    @patch("core.views.logic.password_policy_check")
    @override_settings(URL_CONFIG="domain")
    @override_settings(CAPTCHA_TYPE="")
    @override_settings(ENABLE_ORCID=True)
    def test_register_email_form_valid_redirects_with_next(self, password_check):
        password_check.return_value = None
        post_data = {
            "email": "kjhsaqccxf7qfwirhqia@example.org",
            "password_1": "qsX1roLama3ADotEopfq",
            "password_2": "qsX1roLama3ADotEopfq",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post(
            f"/register/step/1/?next={self.next_url_encoded}",
            post_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)

    @patch("core.views.orcid.get_orcid_record_details")
    @patch("core.views.logic.password_policy_check")
    @override_settings(URL_CONFIG="domain")
    @override_settings(CAPTCHA_TYPE="")
    @override_settings(ENABLE_ORCID=True)
    def test_register_orcid_form_valid_redirects_to_next(
        self, password_check, get_orcid_details
    ):
        get_orcid_details.return_value = {
            "first_name": "New",
            "last_name": "User",
            "emails": ["kjhsaqccxf7qfwirhqia@example.org"],
            "orcid": self.user_orcid,
            "uri": self.user_orcid_uri,
        }
        password_check.return_value = None
        post_data = {
            "first_name": "New",
            "last_name": "User",
            "email": "kjhsaqccxf7qfwirhqia@example.org",
            "password_1": "qsX1roLama3ADotEopfq",
            "password_2": "qsX1roLama3ADotEopfq",
        }
        path = f"/register/step/1/{self.orcid_token_uuid}/"
        query = f"next={self.next_url_encoded}"
        response = self.client.post(
            f"{path}?{query}",
            post_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)


class OrcidRegistrationTests(CoreViewTestsWithData):
    @override_settings(URL_CONFIG="domain")
    def test_login_link_has_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            f"/register/step/orcid/{self.orcid_token_uuid}/",
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            f"/login/?next={self.next_url_encoded}",
            response.content.decode(),
        )

    @override_settings(URL_CONFIG="domain")
    def test_forgot_password_link_has_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            f"/register/step/orcid/{self.orcid_token_uuid}/",
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            f"/reset/step/1/?next={self.next_url_encoded}",
            response.content.decode(),
        )

    @override_settings(URL_CONFIG="domain")
    def test_register_link_has_next(self):
        get_data = {
            "next": self.next_url_raw,
        }
        orcid_registration_path = f"/register/step/orcid/{self.orcid_token_uuid}/"
        response = self.client.get(
            orcid_registration_path,
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            f"/register/step/1/{self.orcid_token_uuid}/?next={self.next_url_encoded}",
            response.content.decode(),
        )


class ActivateAccountTests(CoreViewTestsWithData):
    @patch("core.views.models.Account.objects.get")
    @override_settings(URL_CONFIG="domain")
    def test_activate_success_redirects_with_next(self, objects_get):
        objects_get.return_value = self.user
        post_data = {}
        response = self.client.post(
            f"/register/step/2/12345/?next={self.next_url_encoded}",
            post_data,
            follow=True,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)

    @patch("core.views.models.Account.objects.get")
    @override_settings(URL_CONFIG="domain")
    def test_login_link_has_next(self, objects_get):
        objects_get.return_value = None
        get_data = {
            "next": self.next_url_raw,
        }
        response = self.client.get(
            "/register/step/2/12345/",
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            self.core_login_with_next,
            response.content.decode(),
        )


class ReturnURLTests(CoreViewTestsWithData):
    @override_settings(URL_CONFIG="domain")
    def test_site_nav_account_links_do_not_have_return(self):
        """
        Check that the url_with_return tag has *not* been used
        in the site nav links for login and registration.
        """
        for theme in self.themes:
            response = self.client.get(
                "/",
                data={"theme": theme},
                SERVER_NAME=self.journal_one.domain,
            )
            content = response.content.decode()
            self.assertNotIn("/login/?next=", content)
            self.assertNotIn("/register/step/1/?next=", content)

    @override_settings(URL_CONFIG="domain")
    def test_journal_submissions_account_links_have_return(self):
        """
        Check that the url_with_return tag *has* been used
        in the submission pathway.
        """
        for theme in self.themes:
            response = self.client.get(
                "/submissions/",
                data={"theme": theme},
                SERVER_NAME=self.journal_one.domain,
            )
            content = response.content.decode()
            self.assertIn(f"/login/?next=/submissions/", content)
            self.assertIn(f"/register/step/1/?next=/submissions/", content)


class ControlledAffiliationManagementTests(CoreViewTestsWithData):
    def test_organization_list_view_get(self):
        self.client.force_login(self.user)
        url = "/profile/organization/search/"
        response = self.client.get(url, {})
        template = "admin/core/organization_search.html"
        self.assertTemplateUsed(response, template)

    def test_organization_list_view_post(self):
        self.client.force_login(self.user)
        get_data = {
            "q": "London",
        }
        url = f"/profile/organization/search/"
        response = self.client.get(url, get_data)
        content = response.content.decode()
        self.assertIn(self.name_bbk_uol.value, content)

    def test_organization_name_create_get(self):
        self.client.force_login(self.user)
        url = "/profile/organization_name/create/"
        response = self.client.get(url, {})
        template = "admin/core/organizationname_form.html"
        self.assertTemplateUsed(response, template)

    def test_organization_name_create_post(self):
        self.client.force_login(self.user)
        post_data = {
            "value": "University of Finsbury",
        }
        url = "/profile/organization_name/create/"
        self.client.post(url, post_data, follow=True)
        try:
            core_models.Organization.objects.get(
                custom_label__value="University of Finsbury",
            )
        except core_models.Organization.DoesNotExist:
            self.fail()

    def test_organization_name_update_get(self):
        # Set up custom org with affiliation
        organization = core_models.Organization.objects.create()
        organization_name = core_models.OrganizationName.objects.create(
            value="University of Finsbury",
            custom_label_for=organization,
        )
        affiliation = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            organization=organization,
        )
        self.client.force_login(self.user)
        url = f"/profile/organization_name/{organization_name.pk}/update/"
        response = self.client.get(url, {})
        template = "admin/core/organizationname_form.html"
        self.assertTemplateUsed(response, template)

    def test_organization_name_update_post(self):
        # Set up custom org with affiliation
        organization = core_models.Organization.objects.create()
        organization_name = core_models.OrganizationName.objects.create(
            value="University of Finsbury",
            custom_label_for=organization,
        )
        affiliation = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            organization=organization,
        )

        # Run test
        self.client.force_login(self.user)
        url = f"/profile/organization_name/{organization_name.pk}/update/"
        post_data = {
            "value": "University of Finsbury Park",
        }
        self.client.post(url, post_data, follow=True)
        organization_name.refresh_from_db()
        self.assertEqual(
            organization_name.value,
            "University of Finsbury Park",
        )

    def test_affiliation_create_get(self):
        organization = core_models.Organization.objects.create()
        self.client.force_login(self.user)
        url = f"/profile/organization/{organization.pk}/affiliation/create/"
        response = self.client.get(url, {})
        template = "admin/core/affiliation_form.html"
        self.assertTemplateUsed(response, template)

    def test_affiliation_create_post(self):
        organization = core_models.Organization.objects.create()

        self.client.force_login(self.user)
        post_data = {}
        url = f"/profile/organization/{organization.pk}/affiliation/create/"
        response = self.client.post(url, post_data, follow=True)
        self.assertIn(
            organization, [affil.organization for affil in self.user.affiliations]
        )

    def test_affiliation_update_get(self):
        self.client.force_login(self.user)
        url = f"/profile/affiliation/{self.affiliation.pk}/update/"
        response = self.client.get(url, {})
        template = "admin/core/affiliation_form.html"
        self.assertTemplateUsed(response, template)

    def test_affiliation_update_post(self):
        self.client.force_login(self.user)
        post_data = {
            "title": "New Job Title",
            "department": "New Department",
        }
        affil_id = self.affiliation.pk
        url = f"/profile/affiliation/{affil_id}/update/"
        response = self.client.post(url, post_data, follow=True)
        self.affiliation.refresh_from_db()
        self.assertEqual(self.affiliation.title, "New Job Title")
        self.assertEqual(self.affiliation.department, "New Department")

    def test_affiliation_delete_get(self):
        self.client.force_login(self.user)
        url = f"/profile/affiliation/{self.affiliation.pk}/delete/"
        response = self.client.get(url, {})
        template = "admin/core/affiliation_confirm_remove.html"
        self.assertTemplateUsed(response, template)

    def test_affiliation_delete_post(self):
        self.client.force_login(self.user)
        post_data = {}
        affil_id = self.affiliation.pk
        url = f"/profile/affiliation/{affil_id}/delete/"
        response = self.client.post(url, post_data, follow=True)
        with self.assertRaises(core_models.ControlledAffiliation.DoesNotExist):
            core_models.ControlledAffiliation.objects.get(pk=affil_id)

    @patch("utils.orcid.get_orcid_record")
    def test_affiliation_update_from_orcid_get(self, get_orcid_record):
        get_orcid_record.return_value = helpers.get_orcid_record_all_fields()
        self.client.force_login(self.user)
        get_data = {}
        url = reverse(
            "core_affiliation_update_from_orcid", kwargs={"how_many": "primary"}
        )
        response = self.client.get(url, get_data)
        self.assertEqual(
            response.context["new_affils"][0].__str__(), "California Digital Library"
        )

    @patch("utils.orcid.get_orcid_record")
    def test_affiliation_update_from_orcid_confirmed(self, get_orcid_record):
        get_orcid_record.return_value = helpers.get_orcid_record_all_fields()
        self.client.force_login(self.user)
        post_data = {}
        url = reverse(
            "core_affiliation_update_from_orcid", kwargs={"how_many": "primary"}
        )
        self.client.post(url, post_data, follow=True)
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.primary_affiliation(as_object=False), "California Digital Library"
        )


class AccessibilityModeLoaderTests(TestCase):
    """Tests for the Clarity-override branch in the template Loader."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        # Configure the journal to use a non-Clarity theme so we can confirm
        # the accessibility-mode flag overrides the journal setting.
        setting_handler.save_setting(
            "general", "journal_theme", cls.journal_one, "material"
        )

    def setUp(self):
        # The Loader memoises journal_theme/base_theme via function_cache,
        # which uses the Django cache. Clear it so each test starts fresh.
        django_cache.clear()
        self.factory = RequestFactory()
        # The loader only ever reads `engine.dirs`, so a stub object is
        # sufficient for unit-testing get_theme_dirs.
        self.loader = Loader(engine=SimpleNamespace(dirs=[]))

    def build_request(self, session=None, query=None):
        request = self.factory.get("/", data=query or {})
        request.journal = self.journal_one
        request.repository = None
        request.press = self.press
        request.session = session or {}
        core_middleware.GlobalRequestMiddleware.process_request(request)
        return request

    def test_accessibility_mode_session_serves_clarity(self):
        self.build_request(session={"accessibility_mode": True})
        dirs = self.loader.get_theme_dirs()
        joined = " ".join(dirs)
        self.assertIn("/themes/clarity/templates", joined)
        self.assertNotIn("/themes/material/templates", joined)

    def test_accessibility_mode_off_serves_journal_theme(self):
        self.build_request(session={})
        dirs = self.loader.get_theme_dirs()
        joined = " ".join(dirs)
        self.assertIn("/themes/material/templates", joined)
        self.assertNotIn("/themes/clarity/templates", joined)

    @override_settings(DEBUG=True)
    def test_debug_theme_query_param_wins_over_session(self):
        self.build_request(
            session={"accessibility_mode": True},
            query={"theme": "OLH"},
        )
        dirs = self.loader.get_theme_dirs()
        joined = " ".join(dirs)
        self.assertIn("/themes/OLH/templates", joined)
        self.assertNotIn("/themes/clarity/templates", joined)

    def test_journal_setting_off_disables_loader_override(self):
        setting_handler.save_setting(
            "general", "accessibility_mode", self.journal_one, False
        )
        try:
            self.build_request(session={"accessibility_mode": True})
            dirs = self.loader.get_theme_dirs()
            joined = " ".join(dirs)
            self.assertIn("/themes/material/templates", joined)
            self.assertNotIn("/themes/clarity/templates", joined)
        finally:
            setting_handler.save_setting(
                "general", "accessibility_mode", self.journal_one, True
            )

    def test_authenticated_user_attribute_serves_clarity(self):
        user = helpers.create_regular_user()
        user.accessibility_mode = True
        user.save()
        request = self.factory.get("/")
        request.journal = self.journal_one
        request.repository = None
        request.press = self.press
        request.user = user
        request.session = {}
        core_middleware.GlobalRequestMiddleware.process_request(request)
        dirs = self.loader.get_theme_dirs()
        joined = " ".join(dirs)
        self.assertIn("/themes/clarity/templates", joined)
        self.assertNotIn("/themes/material/templates", joined)


class AccessibilityModeToggleViewTests(TestCase):
    """Tests for the toggle_accessibility_mode view."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.user_email = "a11y_toggle@example.org"
        cls.user_password = "Yk3pNq8wL2vZr7tX"
        cls.user = core_models.Account.objects.create_user(
            cls.user_email,
            password=cls.user_password,
        )
        cls.user.is_active = True
        cls.user.save()

    def setUp(self):
        clear_script_prefix()
        self.client = Client()

    @override_settings(URL_CONFIG="domain")
    def test_anonymous_post_flips_session_value_true_then_false(self):
        url = reverse("toggle_accessibility_mode")

        first = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(first.status_code, 302)
        self.assertTrue(self.client.session.get("accessibility_mode"))

        second = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(second.status_code, 302)
        self.assertFalse(self.client.session.get("accessibility_mode"))

    @override_settings(URL_CONFIG="domain")
    def test_safe_next_url_is_followed(self):
        url = reverse("toggle_accessibility_mode")
        response = self.client.post(
            url,
            {"next": "/about/"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/about/")

    @override_settings(URL_CONFIG="domain")
    def test_unsafe_next_url_falls_back_to_safe_redirect(self):
        url = reverse("toggle_accessibility_mode")
        response = self.client.post(
            url,
            {"next": "https://evil.example.com/steal/"},
            HTTP_REFERER="https://evil.example.com/steal/",
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        # Both `next` and the referer point to a different host, so the view
        # falls back to the root path.
        self.assertEqual(response["Location"], "/")
        self.assertNotIn("evil.example.com", response["Location"])

    @override_settings(URL_CONFIG="domain")
    def test_get_method_is_not_allowed(self):
        url = reverse("toggle_accessibility_mode")
        response = self.client.get(url, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(response.status_code, 405)

    @override_settings(URL_CONFIG="domain")
    def test_journal_setting_off_returns_404(self):
        setting_handler.save_setting(
            "general", "accessibility_mode", self.journal_one, False
        )
        try:
            url = reverse("toggle_accessibility_mode")
            response = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
            self.assertEqual(response.status_code, 404)
            self.assertFalse(self.client.session.get("accessibility_mode"))
        finally:
            setting_handler.save_setting(
                "general", "accessibility_mode", self.journal_one, True
            )

    @override_settings(URL_CONFIG="domain")
    def test_authenticated_post_flips_user_attribute_not_session(self):
        user = helpers.create_regular_user()
        self.client.force_login(user)
        url = reverse("toggle_accessibility_mode")

        first = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(first.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.accessibility_mode)
        self.assertIsNone(self.client.session.get("accessibility_mode"))

        second = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(second.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.accessibility_mode)

    @override_settings(URL_CONFIG="domain")
    def test_login_migrates_session_preference_to_account(self):
        # Enabling accessibility mode while anonymous stores a session flag.
        # On login that preference must be carried onto the account and the
        # session flag cleared, so the two sources can never disagree.
        anon_response = self.client.post(
            reverse("toggle_accessibility_mode"),
            {},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(anon_response.status_code, 302)
        self.assertTrue(self.client.session.get("accessibility_mode"))

        logged_in = self.client.login(
            username=self.user_email,
            password=self.user_password,
        )
        self.assertTrue(logged_in)
        self.user.refresh_from_db()
        self.assertTrue(self.user.accessibility_mode)
        self.assertIsNone(self.client.session.get("accessibility_mode"))

    @override_settings(URL_CONFIG="domain")
    def test_mode_can_be_disabled_after_enabling_then_logging_in(self):
        # Regression test for the reported bug: enabling accessibility mode
        # while anonymous and then logging in must leave the mode disableable.
        # Previously the stale session flag shadowed the account flag, so the
        # toggle re-enabled the account flag instead of disabling the mode.
        self.client.post(
            reverse("toggle_accessibility_mode"),
            {},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertTrue(self.client.session.get("accessibility_mode"))

        self.client.login(
            username=self.user_email,
            password=self.user_password,
        )
        # The preference has migrated onto the account and the mode is active.
        self.user.refresh_from_db()
        self.assertTrue(self.user.accessibility_mode)

        # A single toggle now disables the mode for good.
        self.client.post(
            reverse("toggle_accessibility_mode"),
            {},
            SERVER_NAME=self.journal_one.domain,
        )
        self.user.refresh_from_db()
        self.assertFalse(self.user.accessibility_mode)
        self.assertIsNone(self.client.session.get("accessibility_mode"))


@override_settings(URL_CONFIG="domain")
class AccessibilityModePersistenceTests(TestCase):
    """Login and logout persistence for the accessibility-mode preference.

    These cover the truth tables agreed in review of PR #5314: on login the
    anonymous session preference wins only when the visitor explicitly toggled
    (key present), otherwise the account value stands; on logout the mode is
    sticky and reflects the account's saved value.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.user_email = "a11y_persist@example.org"
        cls.user_password = "Yk3pNq8wL2vZr7tX"
        cls.user = core_models.Account.objects.create_user(
            cls.user_email,
            password=cls.user_password,
        )
        cls.user.is_active = True
        cls.user.save()

    def setUp(self):
        clear_script_prefix()
        self.client = Client()

    def seed_anonymous_session(self, value):
        """Seed the anonymous session flag.

        ``None`` leaves the session untouched (no key, i.e. the visitor never
        toggled); ``True``/``False`` records an explicit anonymous choice.
        """
        if value is None:
            return
        session = self.client.session
        session["accessibility_mode"] = value
        session.save()

    def login_after(self, anonymous, account):
        """Apply an anonymous session state and account flag, then log in."""
        self.user.accessibility_mode = account
        self.user.save()
        self.seed_anonymous_session(anonymous)
        self.assertTrue(
            self.client.login(
                username=self.user_email,
                password=self.user_password,
            )
        )
        self.user.refresh_from_db()

    def assertLoginResult(self, anonymous, account, expected_account):
        self.login_after(anonymous=anonymous, account=account)
        self.assertEqual(self.user.accessibility_mode, expected_account)
        # The session flag is always cleared so it can never shadow the
        # account preference on later requests.
        self.assertIsNone(self.client.session.get("accessibility_mode"))

    def test_login_row_1_untouched_account_off_stays_off(self):
        self.assertLoginResult(
            anonymous=None,
            account=False,
            expected_account=False,
        )

    def test_login_row_2_untouched_account_on_stays_on(self):
        self.assertLoginResult(
            anonymous=None,
            account=True,
            expected_account=True,
        )

    def test_login_row_3_explicit_on_account_off_writes_on(self):
        self.assertLoginResult(
            anonymous=True,
            account=False,
            expected_account=True,
        )

    def test_login_row_4_explicit_on_account_on_stays_on(self):
        self.assertLoginResult(
            anonymous=True,
            account=True,
            expected_account=True,
        )

    def test_login_row_5_explicit_off_account_off_stays_off(self):
        self.assertLoginResult(
            anonymous=False,
            account=False,
            expected_account=False,
        )

    def test_login_row_6_explicit_off_account_on_writes_off(self):
        # The key fix: an explicit anonymous off disables a previously enabled
        # account preference, rather than being indistinguishable from
        # "untouched" and leaving the account on.
        self.assertLoginResult(
            anonymous=False,
            account=True,
            expected_account=False,
        )

    def test_logout_row_1_account_on_stays_on(self):
        self.user.accessibility_mode = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("core_logout"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        # Logout flushes the session; the account value is re-seeded so the
        # mode is sticky for the now-anonymous visitor.
        self.assertTrue(self.client.session.get("accessibility_mode"))

    def test_logout_row_2_account_off_stays_off(self):
        self.user.accessibility_mode = False
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("core_logout"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session.get("accessibility_mode"))


class ControlledAffiliationDisplayTests(CoreViewTestsWithData):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ror_svg_template = get_template("common/svg/ror-mono.svg")
        cls.ror_svg = ror_svg_template.render({})

    def test_all_custom(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        org = core_models.Organization.objects.create()
        core_models.OrganizationName(
            value="Birkbeck",
            custom_label_for=org,
        )
        country, _ = core_models.Country.objects.get_or_create(
            code="GB",
            defaults={"name": "United Kingdom"},
        )
        location, _ = core_models.Location.objects.get_or_create(
            name="London",
            country=country,
        )
        org.locations.add(location)
        affil = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            organization=org,
            title="Reader",
            department="English",
            start=timezone.datetime(2010, 5, 5, tzinfo=timezone.utc),
            end=timezone.datetime(2016, 10, 15, tzinfo=timezone.utc),
        )
        context = {
            "affiliation": affil,
        }
        expected = """
          <li>Reader</li>
          <li>English</li>
          <li itemprop="worksFor" itemscope itemtype="http://schema.org/CollegeOrUniversity">
              <span itemprop="name">
                  <span>Birkbeck</span>
              </span>
          </li>
          <li>London, United Kingdom</li>
        """
        self.assertHTMLEqual(expected, template.render(context))

    def test_title(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        context = {
            "affiliation": core_models.ControlledAffiliation.objects.create(
                account=self.user,
                title="Reader",
            ),
        }
        expected = """
          <li>Reader</li>
        """
        self.assertHTMLEqual(expected, template.render(context))

    def test_department(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        context = {
            "affiliation": core_models.ControlledAffiliation.objects.create(
                account=self.user,
                department="English",
            ),
        }
        expected = """
          <li>English</li>
        """
        self.assertHTMLEqual(expected, template.render(context))

    def test_controlled_org(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        org, _ = core_models.Organization.objects.get_or_create(
            ror_id="02mb95055",
        )
        affil = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            organization=org,
        )
        context = {
            "affiliation": affil,
        }
        expected = f"""
          <li itemprop="worksFor" itemscope itemtype="http://schema.org/CollegeOrUniversity">
            <span itemprop="name">
              <span>Birkbeck, University of London</span>
            </span>
            <a href="https://ror.org/02mb95055" itemprop="url" target="_blank">
              <span class="sr-only show-for-sr">
                View ROR record for Birkbeck, University of London.
              </span>
              <span class="show-for-sr sr-only">(opens in new tab)</span>
              {self.ror_svg}
            </a>
          </li>
        """
        self.assertHTMLEqual(expected, template.render(context))

    def test_custom_org(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        org = core_models.Organization.objects.create()
        core_models.OrganizationName(
            value="Birkbeck",
            custom_label_for=org,
        )
        affil = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            organization=org,
        )
        context = {
            "affiliation": affil,
        }
        expected = """
          <li itemprop="worksFor" itemscope itemtype="http://schema.org/CollegeOrUniversity">
            <span itemprop="name">
              <span>Birkbeck</span>
            </span>
          </li>
        """
        self.assertHTMLEqual(expected, template.render(context))

    def test_location_city(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        org = core_models.Organization.objects.create()
        location, _ = core_models.Location.objects.get_or_create(
            name="London",
        )
        org.locations.add(location)
        affil = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            organization=org,
        )
        context = {
            "affiliation": affil,
        }
        expected = """
          <li>London</li>
        """
        self.assertHTMLEqual(expected, template.render(context))

    def test_location_country(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        org = core_models.Organization.objects.create()
        country, _ = core_models.Country.objects.get_or_create(
            code="GB",
            defaults={"name": "United Kingdom"},
        )
        location, _ = core_models.Location.objects.get_or_create(
            country=country,
        )
        org.locations.add(location)
        affil = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            organization=org,
        )
        context = {
            "affiliation": affil,
        }
        expected = """
          <li>United Kingdom</li>
        """
        self.assertHTMLEqual(expected, template.render(context))

    def test_start(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        affil = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            title="Independent scholar",
            start=timezone.datetime(2010, 5, 5, tzinfo=timezone.utc),
        )
        context = {
            "affiliation": affil,
            "include_dates": True,
        }
        expected = """
          <li>Independent scholar</li>
          <li>May 2010&ndash;</li>
        """
        self.assertHTMLEqual(expected, template.render(context))

    def test_end(self):
        template = get_template("common/elements/affiliation_inner_li_details.html")
        affil = core_models.ControlledAffiliation.objects.create(
            account=self.user,
            title="Independent scholar",
            end=timezone.datetime(2016, 10, 15, tzinfo=timezone.utc),
        )
        context = {
            "affiliation": affil,
            "include_dates": True,
        }
        expected = """
          <li>Independent scholar</li>
          <li>&ndash;Oct 2016</li>
        """
        self.assertHTMLEqual(expected, template.render(context))

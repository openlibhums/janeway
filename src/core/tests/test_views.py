__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from mock import patch
from uuid import uuid4

from django.test import Client, TestCase, override_settings

from utils.testing import helpers

from core import models as core_models


class NextURLTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.theme_dirs = helpers.get_theme_dirs()
        helpers.create_roles(['author'])
        cls.user_email = 'sukv8golcvwervs0y7e5@example.org'
        cls.user_password = 'xUMXW1oXn2l8L26Kixi2'
        cls.user = core_models.Account.objects.create_user(
            cls.user_email,
            password=cls.user_password,
        )
        cls.user.is_active = True
        cls.user_orcid = 'https://orcid.org/0000-0001-2345-6789'
        cls.user.orcid = cls.user_orcid
        cls.orcid_token_str = uuid4()
        cls.orcid_token = core_models.OrcidToken.objects.create(
            token=cls.orcid_token_str,
            orcid=cls.user_orcid,
        )
        cls.reset_token_str = uuid4()
        cls.reset_token = core_models.PasswordResetToken.objects.create(
            account=cls.user,
            token=cls.reset_token_str,
        )
        cls.user.save()

        # The raw unicode string of a 'next' URL
        cls.next_url_raw = '/target/page/?a=b&x=y'

        # The unicode string url-encoded with safe='/'
        cls.next_url_encoded = '/target/page/%3Fa%3Db%26x%3Dy'

        # The unicode string url-encoded with safe=''
        cls.next_url_encoded_no_safe = '%2Ftarget%2Fpage%2F%3Fa%3Db%26x%3Dy'

        # next_url_encoded with its 'next' key
        cls.next_url_query_string = 'next=/target/page/%3Fa%3Db%26x%3Dy'

        # The core_login url with encoded next url
        cls.core_login_with_next = '/login/?next=/target/page/%3Fa%3Db%26x%3Dy'

    def setUp(self):
        self.client = Client()


class UserLoginTests(NextURLTests):

    def test_is_authenticated_redirects_to_next(self):
        self.client.login(username=self.user_email, password=self.user_password)
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch('core.views.authenticate')
    def test_login_success_redirects_to_next(self, authenticate):
        authenticate.return_value = self.user
        data = {
            'user_name': self.user_email,
            'user_pass': self.user_password,
            'next': self.next_url_raw,
        }
        response = self.client.post('/login/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch('utils.template_override_middleware.Loader.get_theme_dirs')
    @override_settings(ENABLE_OIDC=True)
    def test_oidc_link_has_next(self, get_theme_dirs):
        data = {
            'next': self.next_url_raw,
        }
        for theme_dirs in self.theme_dirs:
            get_theme_dirs.return_value = theme_dirs
            response = self.client.get('/login/', data)
            self.assertIn(
                f'/oidc/authenticate/?next={self.next_url_encoded}',
                response.content.decode(),
            )

    @patch('utils.template_override_middleware.Loader.get_theme_dirs')
    @override_settings(ENABLE_ORCID=True)
    def test_orcid_link_has_next(self, get_theme_dirs):
        data = {
            'next': self.next_url_raw,
        }
        for theme_dirs in self.theme_dirs:
            get_theme_dirs.return_value = theme_dirs
            response = self.client.get('/login/', data)
            self.assertIn(
                f'/login/orcid/?next={self.next_url_encoded}',
                response.content.decode(),
            )

    @patch('utils.template_override_middleware.Loader.get_theme_dirs')
    def test_forgot_password_link_has_next(self, get_theme_dirs):
        data = {
            'next': self.next_url_raw,
        }
        for theme_dirs in self.theme_dirs:
            get_theme_dirs.return_value = theme_dirs
            response = self.client.get('/login/', data)
            self.assertIn(
                f'/reset/step/1/?next={self.next_url_encoded}',
                response.content.decode(),
            )

    @patch('utils.template_override_middleware.Loader.get_theme_dirs')
    def test_register_link_has_next(self, get_theme_dirs):
        data = {
            'next': self.next_url_raw,
        }
        for theme_dirs in self.theme_dirs:
            get_theme_dirs.return_value = theme_dirs
            response = self.client.get('/login/', data)
            self.assertIn(
                f'/register/step/1/?next={self.next_url_encoded}',
                response.content.decode(),
            )


class UserLoginOrcidTests(NextURLTests):

    @override_settings(ENABLE_ORCID=False)
    def test_orcid_disabled_redirects_with_next(self):
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn(self.next_url_encoded, response.redirect_chain[0][0])

    @override_settings(ENABLE_ORCID=True)
    def test_no_orcid_code_redirects_with_next(self):
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data)
        self.assertIn(self.next_url_encoded_no_safe, response.url)

    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_orcid_id_account_found_redirects_to_next(
        self,
        retrieve_tokens,
    ):
        retrieve_tokens.return_value = self.user_orcid
        data = {
            'code': '12345',
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch('core.views.orcid.get_orcid_record_details')
    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_orcid_id_no_account_matching_email_redirects_to_next(
        self,
        retrieve_tokens,
        orcid_details,
    ):
        # Change ORCID so it doesn't work
        retrieve_tokens.return_value = 'https://orcid.org/0000-0001-2312-3123'

        # Return an email that will work
        orcid_details.return_value = {'emails': [self.user_email]}

        data = {
            'code': '12345',
            'state': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch('core.views.orcid.get_orcid_record_details')
    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_orcid_id_no_account_no_matching_email_redirects_to_next(
        self,
        retrieve_tokens,
        orcid_details,
    ):
        # Change ORCID so it doesn't work
        retrieve_tokens.return_value = 'https://orcid.org/0000-0001-2312-3123'

        orcid_details.return_value = {'emails': []}
        data = {
            'code': '12345',
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn(
            self.next_url_query_string,
            response.redirect_chain[0][0],
        )

    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_no_orcid_id_retrieved_redirects_with_next(self, retrieve_tokens):
        retrieve_tokens.return_value = None
        data = {
            'code': '12345',
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)


class GetResetTokenTests(NextURLTests):

    @patch('core.views.logic.start_reset_process')
    def test_start_reset_redirects_with_next(self, _start_reset):
        data = {
            'email_address': self.user_email,
            'next': self.next_url_raw,
        }
        response = self.client.post('/reset/step/1/', data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)


class ResetPasswordTests(NextURLTests):

    @patch('core.views.logic.password_policy_check')
    def test_reset_password_form_valid_redirects_with_next(self, password_check):
        password_check.return_value = None
        data = {
            'password_1': 'qsX1roLama3ADotEopfq',
            'password_2': 'qsX1roLama3ADotEopfq',
            'next': self.next_url_raw,
        }
        reset_step_2_path = f'/reset/step/2/{self.reset_token.token}/'
        response = self.client.post(reset_step_2_path, data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)


class RegisterTests(NextURLTests):

    @patch('core.views.logic.password_policy_check')
    @override_settings(CAPTCHA_TYPE='')
    @override_settings(ENABLE_ORCID=True)
    def test_register_email_form_valid_redirects_with_next(self, password_check):
        password_check.return_value = None
        data = {
            'email': 'kjhsaqccxf7qfwirhqia@example.org',
            'password_1': 'qsX1roLama3ADotEopfq',
            'password_2': 'qsX1roLama3ADotEopfq',
            'first_name': 'New',
            'last_name': 'User',
            'next': self.next_url_raw,
        }
        response = self.client.post('/register/step/1/', data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)

    @patch('core.views.orcid.get_orcid_record_details')
    @patch('core.views.logic.password_policy_check')
    @override_settings(CAPTCHA_TYPE='')
    @override_settings(ENABLE_ORCID=True)
    def test_user_register_orcid_form_valid_redirects_to_next(
        self,
        password_check,
        get_orcid_details
    ):
        get_orcid_details.return_value = {
            'first_name': 'New',
            'last_name': 'User',
            'emails': ['kjhsaqccxf7qfwirhqia@example.org'],
        }
        password_check.return_value = None
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'kjhsaqccxf7qfwirhqia@example.org',
            'password_1': 'qsX1roLama3ADotEopfq',
            'password_2': 'qsX1roLama3ADotEopfq',
            'token': self.orcid_token_str,
            'next': self.next_url_raw,
        }
        response = self.client.post('/register/step/1/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)


class OrcidRegistrationTests(NextURLTests):

    @patch('utils.template_override_middleware.Loader.get_theme_dirs')
    def test_login_link_has_next(self, get_theme_dirs):
        data = {
            'next': self.next_url_raw,
        }
        for theme_dirs in self.theme_dirs:
            get_theme_dirs.return_value = theme_dirs
            orcid_registration_path = f'/register/step/orcid/{self.orcid_token_str}/'
            response = self.client.get(orcid_registration_path, data)
            self.assertIn(
                f'/login/?next={self.next_url_encoded}',
                response.content.decode(),
            )

    @patch('utils.template_override_middleware.Loader.get_theme_dirs')
    def test_forgot_password_link_has_next(self, get_theme_dirs):
        data = {
            'next': self.next_url_raw,
        }
        for theme_dirs in self.theme_dirs:
            get_theme_dirs.return_value = theme_dirs
            orcid_registration_path = f'/register/step/orcid/{self.orcid_token_str}/'
            response = self.client.get(orcid_registration_path, data)
            self.assertIn(
                f'/reset/step/1/?next={self.next_url_encoded}',
                response.content.decode(),
            )

    @patch('utils.template_override_middleware.Loader.get_theme_dirs')
    def test_register_link_has_next(self, get_theme_dirs):
        data = {
            'next': self.next_url_raw,
        }
        for theme_dirs in self.theme_dirs:
            get_theme_dirs.return_value = theme_dirs
            orcid_registration_path = f'/register/step/orcid/{self.orcid_token_str}/'
            response = self.client.get(orcid_registration_path, data)
            self.assertIn(
                f'/register/step/1/?next={self.next_url_encoded}&token={self.orcid_token_str}',
                response.content.decode(),
            )


class ToDo:

    @patch('core.views.models.Account.objects.get')
    def test_activate_account_next(self, objects_get):
        objects_get.return_value = self.user
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.post('/register/step/2/12345/', data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)

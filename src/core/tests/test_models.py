from django.db import IntegrityError
from django.test import TestCase

from core import models


class TestAccount(TestCase):
    def test_creation(self):
        data = {
            'email': 'test@test.com',
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Prof.',
            'first_name': 'Martin',
            'last_name': 'Eve',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
        }

        models.Account.objects.create(**data)
        try:
            models.Account.objects.get(email='test@test.com')
        except models.Account.DoesNotExist:
            self.fail('User account has not been created.')

    def test_username_normalised(self):
        email = "TEST@test.com"
        data = {
            'email': email,
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Prof.',
            'first_name': 'Martin',
            'last_name': 'Eve',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
        }
        obj = models.Account.objects.create(**data)
        self.assertEquals(obj.username, email.lower())

    def test_email_normalised(self):
        email = "TEST@TEST.com"
        expected = "TEST@test.com"
        data = {
            'email': email,
        }
        obj = models.Account.objects.create(**data)
        self.assertEquals(obj.email, expected)

    def test_no_duplicates(self):
        email_a = "TEST@TEST.com"
        email_b = "test@TEST.com"
        models.Account.objects.create(email=email_a)
        with self.assertRaises(
            IntegrityError,
            msg="Managed to register account with duplicate email",
        ):
            models.Account.objects.create(email=email_b)

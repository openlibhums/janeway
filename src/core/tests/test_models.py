from django.db import IntegrityError
from django.test import TestCase

from core import models
from core.model_utils import merge_models
from journal import models as journal_models
from utils.testing import helpers


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

    def test_merge_accounts_m2m(self):
        """Test merging of m2m elements when mergint two accounts"""
        # Setup
        from_account = models.Account.objects.create(email="from@test.com")
        to_account = models.Account.objects.create(email="to@test.com")
        interest = models.Interest.objects.create(name="test")
        from_account.interest.add(interest)

        # Test
        merge_models(from_account, to_account)

        # Assert
        self.assertTrue(
            interest in to_account.interest.all(),
            msg="Failed to merge user models",
        )

    def test_merge_accounts_m2m_through(self):
        """Test merging of m2m declaring 'through' when merging two accounts"""
        # Setup
        from_account = models.Account.objects.create(email="from@test.com")
        to_account = models.Account.objects.create(email="to@test.com")
        press = helpers.create_press()
        journal, _ = helpers.create_journals()
        issue = journal_models.Issue.objects.create(journal=journal)

        # Issue editors have a custom through model
        issue_editor = journal_models.IssueEditor.objects.create(
            issue=issue,
            account=from_account,
        )

        # Test
        merge_models(from_account, to_account)

        # Assert
        self.assertTrue(
            to_account.issueeditor_set.filter(issue=issue).exists(),
            msg="Failed to merge user models",
        )

    def test_merge_accounts_o2m(self):
        """Test merging of o2m elements when merging two accounts"""
        # Setup
        press = helpers.create_press()
        journal, _ = helpers.create_journals()
        from_account = models.Account.objects.create(email="from@test.com")
        to_account = models.Account.objects.create(email="to@test.com")
        role = models.AccountRole.objects.create(
            user=from_account,
            journal=journal,
            role=models.Role.objects.create(name="t", slug="t"),
        )

        # Test
        merge_models(from_account, to_account)

        # Assert
        self.assertTrue(
            role in to_account.accountrole_set.all(),
            msg="Failed to merge user models",
        )

    def test_merge_accounts_o2m_unique(self):
        """Test merging of o2m unique elements of two accounts"""
        # Setup
        press = helpers.create_press()
        journal, _ = helpers.create_journals()
        from_account = models.Account.objects.create(email="from@test.com")
        to_account = models.Account.objects.create(email="to@test.com")
        role_obj = models.Role.objects.create(name="t", slug="t")
        role = models.AccountRole.objects.create(
            user=from_account,
            journal=journal,
            role=role_obj,
        )
        unique_violation = models.AccountRole.objects.create(
            user=to_account,
            journal=journal,
            role=role_obj
        )


        # Test
        merge_models(from_account, to_account)

        # Assert
        self.assertTrue(
            unique_violation in to_account.accountrole_set.all(),
            msg="Failed to merge user models",
        )

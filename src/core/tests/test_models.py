from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.forms import Form
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from core import forms, models
from core.model_utils import merge_models, SVGImageFieldForm
from journal import models as journal_models
from utils.testing import helpers
from submission import models as submission_models

FROZEN_DATETIME_20210101 = timezone.make_aware(timezone.datetime(2021, 1, 1, 0, 0, 0))
FROZEN_DATETIME_20210102 = timezone.make_aware(timezone.datetime(2021, 1, 2, 0, 0, 0))
FROZEN_DATETIME_20210103 = timezone.make_aware(timezone.datetime(2021, 1, 3, 0, 0, 0))


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

    def test_username_normalised_quick_form(self):
        email = "QUICK@test.com"
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
        form = forms.QuickUserForm(data=data)
        acc = form.save()
        self.assertEquals(acc.username, email.lower())

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

    def test_no_duplicates_quick_form(self):
        email_a = "TEST@TEST.com"
        email_b = "test@TEST.com"
        data = dict(
            first_name="Test",
            last_name="Last Name",
            email=email_a,
            institution="A.N. Institution",
        )
        form_a = forms.QuickUserForm(data=data)
        form_a.save()
        with self.assertRaises(
            ValueError,
            msg="Managed to quick-register account with duplicate email",
        ):
            form_b = forms.QuickUserForm(data=dict(data, email=email_b))
            form_b.save()

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

    def test_full_name(self):
        author = models.Account.objects.create(
            email='test@example.com',
            first_name='',
            middle_name='',
            last_name='Sky',
        )
        self.assertEqual('Sky', author.full_name())


class TestSVGImageFormField(TestCase):
    def test_upload_svg_to_svg_image_form_field(self):
        svg_data = """
            <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="50"></circle>
            </svg>
        """
        svg_file = SimpleUploadedFile(
            "file.svg",
            svg_data.encode("utf-8"),
        )
        TestForm = type(
            "TestFormForm", (Form,),
            {"file": SVGImageFieldForm()}
        )
        form = TestForm({}, {"file": svg_file})
        self.assertTrue(form.is_valid())

    def test_upload_corrupt_svg_to_svg_image_form_field(self):
        svg_data = """
            <svg">
                corrupt data here
            </svg>
        """
        svg_file = SimpleUploadedFile(
            "file.svg",
            svg_data.encode("utf-8"),
        )
        TestForm = type(
            "TestFormForm", (Form,),
            {"file": SVGImageFieldForm()}
        )
        form = TestForm({}, {"file": svg_file})
        self.assertFalse(form.is_valid())

    def test_upload_image_to_svg_image_form_field(self):
        svg_data = ""
        image_data = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        image_file = SimpleUploadedFile(
            "file.gif",
            image_data,
        )
        TestForm = type(
            "TestFormForm", (Form,),
            {"file": SVGImageFieldForm()}
        )
        form = TestForm({}, {"file": image_file})
        self.assertTrue(form.is_valid())


class TestLastModifiedModel(TestCase):

    def setUp(self):
        self.press = helpers.create_press()
        self.press.save()
        self.journal_one, self.journal_two = helpers.create_journals()
        self.issue = helpers.create_issue(self.journal_one)

        self.article, c = submission_models.Article.objects.get_or_create(
            title='Test Model Utils Article',
        )

    def test_abstract_last_mod_save(self):
        test_abstract_text = 'The Phantom Menace Sucks'
        self.article.abstract = test_abstract_text
        self.article.save()

        self.assertEqual(
            self.article.abstract,
            test_abstract_text
        )

    def test_abstract_last_mod_update_doesnt_die(self):
        article_last_mod = self.article.last_modified

        articles = submission_models.Article.objects.filter(
            pk=self.article.pk
        ).update(
            title='You\'re Wrong About the Phantom Menace'
        )

    def test_last_modified_model(self):
        # prepare
        with freeze_time(FROZEN_DATETIME_20210102):
            issue_date = self.issue.last_modified = (
                timezone.now() - timedelta(days=1)
            )
            self.issue.save()
        with freeze_time(FROZEN_DATETIME_20210101):
            self.article.last_modified = (
                timezone.now() - timedelta(days=2)
            )
            self.article.save()

        # Test
        self.assertEqual(self.article.best_last_modified_date(), issue_date)

    def test_last_modified_model_recursive(self):
        # prepare

        with freeze_time(FROZEN_DATETIME_20210103):
            file_obj = models.File.objects.create()
            file_date = file_obj.las_modified = timezone.now()
            file_obj.save()

        with freeze_time(FROZEN_DATETIME_20210102):
            galley = helpers.create_galley(self.article, file_obj)
            galley.last_modified = timezone.now()
            galley.save()

        with freeze_time(FROZEN_DATETIME_20210101):
            self.article.last_modified = timezone.now()
            self.article.save()
            self.article.refresh_from_db()

        # Test
        self.assertEqual(self.article.best_last_modified_date(), file_date)

    def test_last_modified_model_recursive_circular(self):
        # prepare

        with freeze_time(FROZEN_DATETIME_20210103):
            file_obj = models.File.objects.create()
            file_date = file_obj.las_modified = timezone.now()
            file_obj.save()

        with freeze_time(FROZEN_DATETIME_20210102):
            galley = helpers.create_galley(self.article, file_obj)
            galley.article = self.article
            galley.last_modified = timezone.now()
            galley.save()

        with freeze_time(FROZEN_DATETIME_20210101):
            self.article.last_modified = timezone.now()
            self.article.save()
            self.article.refresh_from_db()

        # Test
        self.assertEqual(self.article.best_last_modified_date(), file_date)

    def test_last_modified_model_recursive_doubly_linked(self):
        with freeze_time(FROZEN_DATETIME_20210103):
            file_obj = models.File.objects.create()
            file_date = file_obj.las_modified = timezone.now()
            file_obj.save()

        with freeze_time(FROZEN_DATETIME_20210102):
            galley = helpers.create_galley(self.article, file_obj)
            galley.article = self.article
            galley.last_modified = timezone.now()
            galley.save()

        with freeze_time(FROZEN_DATETIME_20210101):
            self.article.render_galley = galley
            self.article.last_modified = timezone.now()
            self.article.save()
            self.article.refresh_from_db()

        # Test
        self.assertEqual(self.article.best_last_modified_date(), file_date)

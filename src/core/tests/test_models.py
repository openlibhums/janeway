from datetime import date, timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.http import HttpRequest, QueryDict
from django.forms import Form, ValidationError
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from core import forms, models
from core.model_utils import (
    merge_models,
    SVGImageFieldForm,
    search_model_admin,
)
from journal import models as journal_models
from utils.testing import helpers
from submission import models as submission_models
from repository import models as repository_models

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


class TestModelUtils(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.account = helpers.create_user(
            'Ab6CrWPPxQ7FoLj5dgdH@example.org',
        )

    def test_search_model_admin(self):
        request = HttpRequest()
        request.GET = QueryDict('q=Ab6CrWPPxQ7FoLj5dgdH')
        results, _duplicates = search_model_admin(
            request,
            models.Account,
        )
        self.assertIn(
            self.account,
            results,
        )


class TestOrganizationModels(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.repo_manager = helpers.create_user(
            'xulz5vepggxdvo8ngirw@example.org'
        )
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain='odhstswzfesoyhhjywzk.example.org',
        )
        cls.country_gb = models.Country.objects.create(
            code='GB',
            name='United Kingdom',
        )
        cls.location_london = models.Location.objects.create(
            name='London',
            country=cls.country_gb,
            latitude=51.50853,
            longitude=-0.12574,
        )
        cls.location_farnborough = models.Location.objects.create(
            name='Farnborough',
            country=cls.country_gb,
            latitude=51.29,
            longitude=-0.75,
        )
        cls.organization_bbk = models.Organization.objects.create(
            ror='https://ror.org/02mb95055',
        )
        cls.name_bbk_uol = models.OrganizationName.objects.create(
            value='Birkbeck, University of London',
            language='en',
            ror_display_for=cls.organization_bbk,
            label_for=cls.organization_bbk,
        )
        cls.name_bbk_cy = models.OrganizationName.objects.create(
            value='Birkbeck, Prifysgol Llundain',
            language='cy',
            label_for=cls.organization_bbk,
        )
        cls.name_bbk_custom = models.OrganizationName.objects.create(
            value='Birkbeck',
            custom_label_for=cls.organization_bbk,
        )
        cls.name_bbk_college = models.OrganizationName.objects.create(
            value='Birkbeck College',
            language='en',
            alias_for=cls.organization_bbk,
        )
        cls.organization_bbk.locations.add(cls.location_london)
        cls.organization_rae = models.Organization.objects.create(
            ror='https://ror.org/0n7v1dg93',
        )
        cls.name_rae = models.OrganizationName.objects.create(
            value='Royal Aircraft Establishment',
            language='en',
            label_for=cls.organization_rae,
            ror_display_for=cls.organization_rae
        )
        cls.organization_rae.locations.add(cls.location_farnborough)
        cls.organization_brp = models.Organization.objects.create(
            ror='https://ror.org/0w7120h04',
        )
        cls.name_brp = models.OrganizationName.objects.create(
            value='British Rubber Producers',
            language='en',
            label_for=cls.organization_brp,
            ror_display_for=cls.organization_brp,
        )
        cls.kathleen_booth = helpers.create_user(
            'ehqak6rxknzw35ih47oc@bbk.ac.uk',
            first_name='Kathleen',
            last_name='Booth',
        )
        cls.kathleen_booth_frozen = submission_models.FrozenAuthor.objects.create(
            first_name='Kathleen',
            last_name='Booth',
            author=cls.kathleen_booth,
            frozen_email='ehqak6rxknzw35ih47oc@bbk.ac.uk',
        )
        cls.preprint_one = helpers.create_preprint(
            cls.repository,
            cls.kathleen_booth,
            cls.subject,
            title='Preprint for testing affiliations',
        )
        cls.kathleen_booth_preprint, _created = repository_models.PreprintAuthor.objects.get_or_create(
            preprint=cls.preprint_one,
            account=cls.kathleen_booth,
        )
        cls.affiliation_lecturer = models.Affiliation.objects.create(
            account=cls.kathleen_booth,
            title='Lecturer',
            department='Department of Numerical Automation',
            organization=cls.organization_bbk,
            is_primary=True,
            start=date.fromisoformat('1952-01-01'),
            end=date.fromisoformat('1962-12-31'),
        )
        cls.affiliation_lecturer_frozen = models.Affiliation.objects.create(
            frozen_author=cls.kathleen_booth_frozen,
            title='Lecturer',
            department='Department of Numerical Automation',
            organization=cls.organization_bbk,
            is_primary=True,
        )
        cls.affiliation_lecturer_preprint = models.Affiliation.objects.create(
            preprint_author=cls.kathleen_booth_preprint,
            title='Lecturer',
            department='Department of Numerical Automation',
            organization=cls.organization_bbk,
            is_primary=True,
        )
        cls.affiliation_scientist = models.Affiliation.objects.create(
            account=cls.kathleen_booth,
            department='Research Association',
            organization=cls.organization_brp,
        )
        cls.affiliation_officer = models.Affiliation.objects.create(
            account=cls.kathleen_booth,
            title='Junior Scientific Officer',
            organization=cls.organization_rae,
            start=date.fromisoformat('1944-01-01'),
        )
        cls.t_s_eliot = helpers.create_user(
            'gene8rahhnmmitlvqiz9@bbk.ac.uk',
            first_name='Thomas',
            middle_name='Stearns',
            last_name='Eliot',
        )

        return super().setUpTestData()

    def test_account_institution_getter(self):
        self.assertEqual(
            self.kathleen_booth.institution,
            'Birkbeck, University of London, London, United Kingdom',
        )

    def test_frozen_author_institution_getter(self):
        self.assertEqual(
            self.kathleen_booth_frozen.institution,
            'Birkbeck, University of London, London, United Kingdom',
        )

    def test_account_institution_setter_canonical_label(self):
        self.t_s_eliot.institution = 'Birkbeck, University of London'
        self.assertEqual(
            self.organization_bbk,
            self.t_s_eliot.affiliation(obj=True).organization,
        )

    def test_account_institution_setter_canonical_alias(self):
        self.t_s_eliot.institution = 'Birkbeck College'
        self.assertEqual(
            self.organization_bbk,
            self.t_s_eliot.affiliation(obj=True).organization,
        )

    def test_account_institution_setter_custom_overwrite(self):
        self.t_s_eliot.institution = 'Birkbek'
        misspelled_bbk = models.Organization.objects.get(
            custom_label__value='Birkbek'
        )
        self.t_s_eliot.institution = 'Birkbck'
        self.assertEqual(
            misspelled_bbk,
            self.t_s_eliot.affiliation(obj=True).organization,
        )

    def test_account_institution_setter_custom_value(self):
        self.kathleen_booth.institution = 'Birkbeck McMillan'
        bbk_mcmillan = models.Organization.objects.get(
            custom_label__value='Birkbeck McMillan'
        )
        self.assertEqual(
            bbk_mcmillan,
            self.kathleen_booth.affiliation(obj=True).organization,
        )

    def test_frozen_author_institution_setter_custom_value(self):
        self.kathleen_booth_frozen.institution = 'Birkbeck McMillan'
        bbk_mcmillan = models.Organization.objects.get(
            custom_label__value='Birkbeck McMillan'
        )
        self.assertEqual(
            bbk_mcmillan,
            self.kathleen_booth_frozen.affiliation(obj=True).organization,
        )

    def test_account_department_getter(self):
        self.assertEqual(
            self.kathleen_booth.department,
            'Department of Numerical Automation',
        )

    def test_frozen_author_department_getter(self):
        self.assertEqual(
            self.kathleen_booth_frozen.department,
            'Department of Numerical Automation',
        )

    def test_account_department_setter(self):
        self.kathleen_booth.department = 'Computer Science'
        self.assertEqual(
            models.Affiliation.objects.get(department='Computer Science'),
            self.kathleen_booth.affiliation(obj=True),
        )

    def test_account_department_setter_updates_existing_primary(self):
        self.affiliation_lecturer.is_primary = True
        self.affiliation_lecturer.save()
        self.kathleen_booth.department = 'Computer Science'
        self.affiliation_lecturer.refresh_from_db()
        self.assertEqual(
            self.affiliation_lecturer.department,
            self.kathleen_booth.affiliation(obj=True).department,
        )

    def test_frozen_author_department_setter(self):
        self.kathleen_booth_frozen.department = 'Computer Science'
        self.assertEqual(
            models.Affiliation.objects.get(department='Computer Science'),
            self.kathleen_booth_frozen.affiliation(obj=True),
        )

    def test_organization_name_ror_display(self):
        self.assertEqual(
            self.organization_bbk.name,
            self.name_bbk_uol,
        )

    def test_organization_name_label(self):
        self.name_bbk_custom.delete()
        self.name_bbk_uol.ror_display_for = None
        self.name_bbk_uol.save()
        self.organization_bbk.refresh_from_db()
        self.assertEqual(
            self.organization_bbk.name,
            self.name_bbk_uol,
        )
        self.name_bbk_uol.delete()
        self.organization_bbk.refresh_from_db()
        self.assertEqual(
            self.organization_bbk.name,
            self.name_bbk_cy,
        )

    def test_organization_name_custom_label(self):
        self.name_bbk_uol.delete()
        self.organization_bbk.refresh_from_db()
        self.assertEqual(
            self.organization_bbk.name,
            self.name_bbk_custom,
        )

    def test_ror_validation(self):
        for invalid_ror in [
            # URLValidator
            '0v2w8z018',
            'ror.org/0v2w8z018',
             # validate_ror
            'https://ror.org/0123456789',
            'https://ror.org/0lu42o079',
            'https://ror.org/abcdefghj',
        ]:
            with self.assertRaises(ValidationError):
                org = models.Organization.objects.create(ror=invalid_ror)
                org.clean_fields()

    def test_account_affiliation_with_primary(self):
        self.assertEqual(
            self.kathleen_booth.affiliation(),
            'Lecturer, Department of Numerical Automation, Birkbeck, University of London, London, United Kingdom',
        )

    def test_account_affiliation_with_no_title(self):
        self.affiliation_lecturer.title = ''
        self.affiliation_lecturer.save()
        self.assertEqual(
            self.kathleen_booth.affiliation(),
            'Department of Numerical Automation, Birkbeck, University of London, London, United Kingdom',
        )

    def test_account_affiliation_with_no_country(self):
        self.location_london.country = None
        self.location_london.save()
        self.assertEqual(
            self.kathleen_booth.affiliation(),
            'Lecturer, Department of Numerical Automation, Birkbeck, University of London, London',
        )

    def test_account_affiliation_with_no_location(self):
        self.organization_bbk.locations.remove(self.location_london)
        self.assertEqual(
            self.kathleen_booth.affiliation(),
            'Lecturer, Department of Numerical Automation, Birkbeck, University of London',
        )

    def test_account_affiliation_with_no_organization(self):
        self.affiliation_lecturer.organization = None
        self.affiliation_lecturer.save()
        self.assertEqual(
            self.kathleen_booth.affiliation(),
            'Lecturer, Department of Numerical Automation',
        )

    def test_account_affiliation_for_past_date(self):
        year_1950 = date.fromisoformat('1950-01-01')
        self.assertEqual(
            self.kathleen_booth.affiliation(date=year_1950),
            'Junior Scientific Officer, Royal Aircraft Establishment, Farnborough, United Kingdom',
        )

    def test_account_affiliation_with_no_primary(self):
        self.affiliation_lecturer.is_primary = False
        self.affiliation_lecturer.save()
        self.assertEqual(
            self.kathleen_booth.affiliation(),
            'Junior Scientific Officer, Royal Aircraft Establishment, Farnborough, United Kingdom',
        )

    def test_account_affiliation_with_no_dates_and_no_primary(self):
        self.affiliation_lecturer.is_primary = False
        self.affiliation_lecturer.start = None
        self.affiliation_lecturer.end = None
        self.affiliation_lecturer.save()
        self.affiliation_officer.start = None
        self.affiliation_officer.save()
        self.assertEqual(
            self.kathleen_booth.affiliation(),
            'Junior Scientific Officer, Royal Aircraft Establishment, Farnborough, United Kingdom',
        )

    def test_account_affiliation_with_no_affiliations(self):
        self.affiliation_lecturer.delete()
        self.affiliation_officer.delete()
        self.affiliation_scientist.delete()
        self.assertEqual(
            self.kathleen_booth.affiliation(),
            '',
        )

    def test_account_affiliation_obj_true(self):
        self.affiliation_lecturer.delete()
        self.assertEqual(
            self.kathleen_booth.affiliation(obj=True),
            self.affiliation_officer,
        )

    def test_frozen_author_affiliation(self):
        self.assertEqual(
            self.kathleen_booth_frozen.affiliation(obj=True),
            self.affiliation_lecturer_frozen,
        )

    def test_preprint_author_affiliation_getter(self):
        self.assertEqual(
            self.kathleen_booth_preprint.affiliation,
            str(self.affiliation_lecturer_preprint),
        )

    def test_preprint_author_affiliation_setter(self):
        self.kathleen_booth_preprint.affiliation = 'Birkbeck McMillan'
        self.kathleen_booth_preprint.refresh_from_db()
        self.assertEqual(
            str(self.kathleen_booth_preprint.affiliation),
            'Birkbeck McMillan'
        )

    @patch('core.models.timezone.now')
    def test_affiliation_is_current(self, now):
        now.return_value = date.fromisoformat('1963-01-31')
        self.assertFalse(self.affiliation_lecturer.is_current)
        self.assertTrue(self.affiliation_scientist.is_current)
        self.assertTrue(self.affiliation_officer.is_current)

    def test_organization_location(self):
        self.assertEqual(
            self.organization_bbk.location,
            self.location_london,
        )

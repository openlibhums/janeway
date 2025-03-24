from datetime import date, timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.db.transaction import TransactionManagementError
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

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)

    def test_creation(self):
        data = {
            'email': 'test@test.com',
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Prof.',
            'first_name': 'Martin',
            'last_name': 'Eve',
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
        issue = journal_models.Issue.objects.create(journal=self.journal_one)

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
        from_account = models.Account.objects.create(email="from@test.com")
        to_account = models.Account.objects.create(email="to@test.com")
        role = models.AccountRole.objects.create(
            user=from_account,
            journal=self.journal_one,
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
        from_account = models.Account.objects.create(email="from@test.com")
        to_account = models.Account.objects.create(email="to@test.com")
        role_obj = models.Role.objects.create(name="t", slug="t")
        role = models.AccountRole.objects.create(
            user=from_account,
            journal=self.journal_one,
            role=role_obj,
        )
        unique_violation = models.AccountRole.objects.create(
            user=to_account,
            journal=self.journal_one,
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

    def test_snapshot_self_first_time(self):
        author = helpers.create_author(
            self.journal_one,
            first_name='Bob',
        )
        self.article_one.authors.add(author)
        self.article_one.correspondence_author = author
        self.article_one.save()

        author.snapshot_self(self.article_one)
        self.assertEqual(
            self.article_one.frozen_authors().first().first_name,
            'Bob',
        )

    def test_snapshot_self_second_time_with_force_update(self):
        author = helpers.create_author(
            self.journal_one,
            first_name='Bob',
        )
        self.article_one.authors.add(author)
        self.article_one.correspondence_author = author
        self.article_one.save()

        # Initial snapshot
        author.snapshot_self(self.article_one)

        # Change author name and re-snapshot with force update
        author.first_name = 'Robert'
        author.save()
        author.snapshot_self(self.article_one, force_update=True)
        self.assertEqual(
            self.article_one.frozen_authors().first().first_name,
            'Robert',
        )


    def test_snapshot_self_second_time_without_force_update(self):
        author = helpers.create_author(
            self.journal_one,
            first_name='Bob',
        )
        self.article_one.authors.add(author)
        self.article_one.correspondence_author = author
        self.article_one.save()

        # Initial snapshot
        author.snapshot_self(self.article_one)

        # Change author name and re-snapshot with no force update
        author.first_name = 'Robert'
        author.save()
        author.snapshot_self(self.article_one, force_update=False)
        self.assertEqual(
            self.article_one.frozen_authors().first().first_name,
            'Bob',
        )


    def test_snapshot_credit_first_time(self):
        author = helpers.create_author(self.journal_one)
        self.article_one.authors.add(author)
        self.article_one.correspondence_author = author
        self.article_one.save()
        author.add_credit('conceptualization', self.article_one)
        author.add_credit('data-curation', self.article_one)

        frozen_author, _ = submission_models.FrozenAuthor.objects.get_or_create(
            author=author,
            article=self.article_one,
        )
        author.snapshot_credit(self.article_one, frozen_author)
        frozen_author_credits = [
            credit.get_role_display() for credit in frozen_author.credits()
        ]
        self.assertIn('Conceptualization', frozen_author_credits)
        self.assertIn('Data Curation', frozen_author_credits)


    def test_snapshot_credit_force_update(self):
        author = helpers.create_author(self.journal_one)
        self.article_one.authors.add(author)
        self.article_one.correspondence_author = author
        self.article_one.save()
        author.add_credit('conceptualization', self.article_one)
        author.add_credit('data-curation', self.article_one)

        frozen_author, _ = submission_models.FrozenAuthor.objects.get_or_create(
            author=author,
            article=self.article_one,
        )
        # Initial snapshot
        author.snapshot_credit(self.article_one, frozen_author)

        # Change the author credits
        author.remove_credit('data-curation', self.article_one)
        author.add_credit('methodology', self.article_one)

        # Snapshot again
        author.snapshot_credit(self.article_one, frozen_author)

        frozen_author_credits = [
            credit.get_role_display() for credit in frozen_author.credits()
        ]
        self.assertIn('Conceptualization', frozen_author_credits)
        self.assertIn('Methodology', frozen_author_credits)
        self.assertNotIn('Data Curation', frozen_author_credits)

    def test_credits(self):
        author = helpers.create_author(self.journal_one)
        self.article_one.authors.add(author)
        author.add_credit('conceptualization', self.article_one)
        self.assertEqual(
            author.credits(article=self.article_one).first().get_role_display(),
            'Conceptualization',
        )


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
        cls.country_us = models.Country.objects.create(
            code='US',
            name='United States',
        )
        cls.location_london = models.Location.objects.create(
            name='London',
            country=cls.country_gb,
        )
        cls.location_farnborough = models.Location.objects.create(
            name='Farnborough',
            country=cls.country_gb,
        )
        cls.location_uk_legacy = models.Location.objects.create(
            # Before integrating ROR we used country-wide locations
            # with no geonames ID or coordinates
            country=cls.country_gb,
        )
        cls.organization_bbk = models.Organization.objects.create(
            ror_id='02mb95055',
        )
        cls.name_bbk_uol = models.OrganizationName.objects.create(
            value='Birkbeck, University of London',
            language='eng',
            ror_display_for=cls.organization_bbk,
            label_for=cls.organization_bbk,
        )
        cls.name_bbk_cym = models.OrganizationName.objects.create(
            value='Birkbeck, Prifysgol Llundain',
            language='cym',
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
            ror_id='0n7v1dg93',
        )
        cls.name_rae = models.OrganizationName.objects.create(
            value='Royal Aircraft Establishment',
            language='en',
            label_for=cls.organization_rae,
            ror_display_for=cls.organization_rae
        )
        cls.organization_rae.locations.add(cls.location_farnborough)
        cls.organization_brp = models.Organization.objects.create(
            ror_id='0w7120h04',
        )
        cls.name_brp = models.OrganizationName.objects.create(
            value='British Rubber Producers',
            language='en',
            label_for=cls.organization_brp,
            ror_display_for=cls.organization_brp,
        )
        cls.organization_bbk_legacy = models.Organization.objects.create(
            # Before integrating ROR we used institution names with no ROR IDs
        )
        cls.organization_bbk_legacy.locations.add(cls.location_uk_legacy)
        cls.name_bbk_custom_legacy = models.OrganizationName.objects.create(
            value='Birkbeck, University of London',
            custom_label_for=cls.organization_bbk_legacy,
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
        cls.affiliation_lecturer = models.ControlledAffiliation.objects.create(
            account=cls.kathleen_booth,
            title='Lecturer',
            department='Department of Numerical Automation',
            organization=cls.organization_bbk,
            is_primary=True,
            start=date.fromisoformat('1952-01-01'),
            end=date.fromisoformat('1962-12-31'),
        )
        cls.affiliation_lecturer_frozen = models.ControlledAffiliation.objects.create(
            frozen_author=cls.kathleen_booth_frozen,
            title='Lecturer',
            department='Department of Numerical Automation',
            organization=cls.organization_bbk,
            is_primary=True,
        )
        cls.affiliation_lecturer_preprint = models.ControlledAffiliation.objects.create(
            preprint_author=cls.kathleen_booth_preprint,
            title='Lecturer',
            department='Department of Numerical Automation',
            organization=cls.organization_bbk,
            is_primary=True,
        )
        cls.affiliation_scientist = models.ControlledAffiliation.objects.create(
            account=cls.kathleen_booth,
            department='Research Association',
            organization=cls.organization_brp,
        )
        cls.affiliation_officer = models.ControlledAffiliation.objects.create(
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
        cls.e_hobsbawm = helpers.create_user(
            'dp0dcbdgtzq4e7ml50fe@example.org',
            first_name='Eric',
            last_name='Hobsbawm',
        )
        cls.affiliation_historian = models.ControlledAffiliation.objects.create(
            account=cls.e_hobsbawm,
            title='Historian',
            organization=cls.organization_bbk_legacy,
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
            self.t_s_eliot.primary_affiliation().organization,
        )

    def test_account_institution_setter_canonical_alias(self):
        self.t_s_eliot.institution = 'Birkbeck College'
        self.assertEqual(
            self.organization_bbk,
            self.t_s_eliot.primary_affiliation().organization,
        )

    def test_account_institution_setter_custom_overwrite(self):
        self.t_s_eliot.institution = 'Birkbek'
        misspelled_bbk = models.Organization.objects.get(
            custom_label__value='Birkbek'
        )
        self.t_s_eliot.institution = 'Birkbck'
        self.assertEqual(
            misspelled_bbk,
            self.t_s_eliot.primary_affiliation().organization,
        )

    def test_account_institution_setter_custom_value(self):
        self.kathleen_booth.institution = 'Birkbeck McMillan'
        bbk_mcmillan = models.Organization.objects.get(
            custom_label__value='Birkbeck McMillan'
        )
        self.assertEqual(
            bbk_mcmillan,
            self.kathleen_booth.primary_affiliation().organization,
        )

    def test_frozen_author_institution_setter_custom_value(self):
        self.kathleen_booth_frozen.institution = 'Birkbeck McMillan'
        bbk_mcmillan = models.Organization.objects.get(
            custom_label__value='Birkbeck McMillan'
        )
        self.assertEqual(
            bbk_mcmillan,
            self.kathleen_booth_frozen.primary_affiliation().organization,
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
            models.ControlledAffiliation.objects.get(
                department='Computer Science',
            ),
            self.kathleen_booth.primary_affiliation(),
        )

    def test_account_department_setter_updates_existing_primary(self):
        self.affiliation_lecturer.is_primary = True
        self.affiliation_lecturer.save()
        self.kathleen_booth.department = 'Computer Science'
        self.affiliation_lecturer.refresh_from_db()
        self.assertEqual(
            self.affiliation_lecturer.department,
            self.kathleen_booth.primary_affiliation().department,
        )

    def test_frozen_author_department_setter(self):
        self.kathleen_booth_frozen.department = 'Computer Science'
        self.assertEqual(
            models.ControlledAffiliation.objects.get(
                department='Computer Science',
            ),
            self.kathleen_booth_frozen.primary_affiliation(),
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
            self.name_bbk_cym,
        )

    def test_organization_name_custom_label(self):
        self.name_bbk_uol.delete()
        self.organization_bbk.refresh_from_db()
        self.assertEqual(
            self.organization_bbk.name,
            self.name_bbk_custom,
        )

    def test_organization_name_language(self):
        name_in_german = models.OrganizationName.objects.create(
            value='Birkbeck in German',
            language='deu',
            label_for=self.organization_bbk,
        )
        self.assertEqual(name_in_german.get_language_display(), 'German')

    def test_ror_validation(self):
        for invalid_ror in [
            '0123456789',
            '0lu42o079',
            'abcdefghj',
        ]:
            with self.assertRaises(ValidationError):
                org = models.Organization.objects.create(ror_id=invalid_ror)
                org.clean_fields()

    def test_account_affiliation_with_primary(self):
        self.assertEqual(
            self.kathleen_booth.primary_affiliation(as_object=False),
            'Lecturer, Department of Numerical Automation, Birkbeck, University of London, London, United Kingdom',
        )

    def test_account_affiliation_with_no_title(self):
        self.affiliation_lecturer.title = ''
        self.affiliation_lecturer.save()
        self.assertEqual(
            self.kathleen_booth.primary_affiliation(as_object=False),
            'Department of Numerical Automation, Birkbeck, University of London, London, United Kingdom',
        )

    def test_account_affiliation_with_no_country(self):
        self.location_london.country = None
        self.location_london.save()
        self.assertEqual(
            self.kathleen_booth.primary_affiliation(as_object=False),
            'Lecturer, Department of Numerical Automation, Birkbeck, University of London, London',
        )

    def test_account_affiliation_with_no_location(self):
        self.organization_bbk.locations.remove(self.location_london)
        self.assertEqual(
            self.kathleen_booth.primary_affiliation(as_object=False),
            'Lecturer, Department of Numerical Automation, Birkbeck, University of London',
        )

    def test_account_affiliation_with_no_organization(self):
        self.affiliation_lecturer.organization = None
        self.affiliation_lecturer.save()
        self.assertEqual(
            self.kathleen_booth.primary_affiliation(as_object=False),
            'Lecturer, Department of Numerical Automation',
        )

    def test_account_affiliation_with_no_primary(self):
        self.affiliation_lecturer.is_primary = False
        self.affiliation_lecturer.save()
        self.assertEqual(
            self.kathleen_booth.primary_affiliation(as_object=False),
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
            self.kathleen_booth.primary_affiliation(as_object=False),
            'Junior Scientific Officer, Royal Aircraft Establishment, Farnborough, United Kingdom',
        )

    def test_account_affiliation_with_no_affiliations(self):
        self.affiliation_lecturer.delete()
        self.affiliation_officer.delete()
        self.affiliation_scientist.delete()
        self.assertEqual(
            self.kathleen_booth.primary_affiliation(as_object=False),
            '',
        )

    def test_account_affiliation_obj_true(self):
        self.affiliation_lecturer.delete()
        self.assertEqual(
            self.kathleen_booth.primary_affiliation(),
            self.affiliation_officer,
        )

    def test_frozen_author_affiliation(self):
        self.assertEqual(
            self.kathleen_booth_frozen.primary_affiliation(),
            self.affiliation_lecturer_frozen,
        )

    def test_preprint_author_affiliation_getter(self):
        self.assertEqual(
            self.kathleen_booth_preprint.primary_affiliation(as_object=False),
            str(self.affiliation_lecturer_preprint),
        )

    def test_preprint_author_affiliation_setter(self):
        self.kathleen_booth_preprint.affiliation = 'Birkbeck McMillan'
        self.assertIn(
            'Birkbeck McMillan',
            self.kathleen_booth_preprint.primary_affiliation(as_object=False),
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

    def test_set_primary_if_first_true(self):
        first_affiliation, _created = models.ControlledAffiliation.objects.get_or_create(
            account=self.t_s_eliot,
            organization=self.organization_bbk,
        )
        self.assertTrue(first_affiliation.is_primary)

    def test_set_primary_if_first_false(self):
        _first_affiliation, _created = models.ControlledAffiliation.objects.get_or_create(
            account=self.t_s_eliot,
            organization=self.organization_bbk,
        )
        second_affiliation, _created = models.ControlledAffiliation.objects.get_or_create(
            account=self.t_s_eliot,
            organization=self.organization_rae,
        )
        self.assertFalse(second_affiliation.is_primary)

    def test_affiliation_save_checks_exclusive_fields(self):
        with self.assertRaises((IntegrityError, TransactionManagementError)):
            models.ControlledAffiliation.objects.create(
                account=self.kathleen_booth,
                frozen_author=self.kathleen_booth_frozen,
                organization=self.organization_bbk,
            )
        with self.assertRaises((IntegrityError, TransactionManagementError)):
            models.ControlledAffiliation.objects.create(
                account=self.kathleen_booth,
                preprint_author=self.kathleen_booth_preprint,
                organization=self.organization_bbk,
            )

    def test_affiliation_get_or_create_without_ror(self):
        affiliation, _created = models.ControlledAffiliation.get_or_create_without_ror(
            institution='Birkbeck Coll',
            department='Computer Sci',
            country='GB',
        )
        self.assertEqual(
            models.Organization.objects.get(
                custom_label__value='Birkbeck Coll'
            ),
            affiliation.organization,
        )
        self.assertEqual(
            'Computer Sci',
            affiliation.department,
        )
        self.assertIn(
            models.Location.objects.get(
                name='',
                country__code='GB'
            ),
            affiliation.organization.locations.all(),
        )

    def test_affiliation_get_or_create_without_ror_value_error(self):
        unsaved_frozen_author = submission_models.FrozenAuthor()
        affil, _ = models.ControlledAffiliation.get_or_create_without_ror(
            institution='Birkbeck College',
            frozen_author=unsaved_frozen_author,
        )
        self.assertEqual(affil, None)

    def test_affiliation_get_or_create_without_ror_integrity_error(self):
        affil, _ = models.ControlledAffiliation.get_or_create_without_ror(
            institution='Birkbeck College',
            account=self.kathleen_booth,
            frozen_author=self.kathleen_booth_frozen,
        )
        self.assertEqual(affil, None)

    def test_account_queryset_deprecated_fields(self):
        kwargs = {
            'email': 'twlwpky6omkqdsc40zlm@example.org',
            'institution': 'Yale',
            'department': 'English',
            'country': 'US',
        }
        with self.assertWarns(DeprecationWarning):
            models.Account.objects.create(**kwargs)

    def test_frozen_author_queryset_deprecated_fields(self):
        kwargs = {
            'frozen_email': 'twlwpky6omkqdsc40zlm@example.org',
            'institution': 'Yale',
            'department': 'English',
            'country': 'US',
        }
        with self.assertWarns(DeprecationWarning):
            submission_models.FrozenAuthor.objects.create(**kwargs)

    def test_preprint_author_queryset_deprecated_fields(self):
        kwargs = {
            'preprint': self.preprint_one,
            'account': self.t_s_eliot,
            'affiliation': 'Birkbeck',
        }
        with self.assertWarns(DeprecationWarning):
            repository_models.PreprintAuthor.objects.create(**kwargs)

    def test_account_queryset_get_or_create(self):
        kwargs = {
            'first_name': 'Michael',
            'last_name': 'Warner',
            'email': 'twlwpky6omkqdsc40zlm@example.org',
            'institution': 'Yale',
            'department': 'English',
            'country': self.country_us,
        }
        account, _created = models.Account.objects.get_or_create(**kwargs)
        self.assertListEqual(
            list(kwargs.values()),
            [
                account.first_name,
                account.last_name,
                account.email,
                account.primary_affiliation().organization.custom_label.value,
                account.primary_affiliation().department,
                account.primary_affiliation().organization.locations.first().country,
            ]
        )

    def test_frozen_author_queryset_get_or_create(self):
        kwargs = {
            'first_name': 'Michael',
            'last_name': 'Warner',
            'frozen_email': 'twlwpky6omkqdsc40zlm@example.org',
            'institution': 'Yale',
            'department': 'English',
            'country': self.country_us,
        }
        frozen_author, _ = submission_models.FrozenAuthor.objects.get_or_create(
            **kwargs
        )
        self.assertListEqual(
            list(kwargs.values()),
            [
                frozen_author.first_name,
                frozen_author.last_name,
                frozen_author.frozen_email,
                frozen_author.primary_affiliation().organization.custom_label.value,
                frozen_author.primary_affiliation().department,
                frozen_author.primary_affiliation().organization.locations.first().country,
            ]
        )

    def test_preprint_author_queryset_get_or_create(self):
        kwargs = {
            'preprint': self.preprint_one,
            'account': self.t_s_eliot,
            'affiliation': 'Birkbeck',
        }
        preprint_author, _ = repository_models.PreprintAuthor.objects.get_or_create(
            **kwargs
        )
        self.assertListEqual(
            list(kwargs.values()),
            [
                preprint_author.preprint,
                preprint_author.account,
                preprint_author.primary_affiliation(as_object=False),
            ]
        )

    def test_account_queryset_get(self):
        self.assertTrue(
            models.Account.objects.get(
                institution__contains='Birkbeck, Prifysgol Llundain',
            )
        )

    def test_frozen_author_queryset_get(self):
        self.assertTrue(
            submission_models.FrozenAuthor.objects.get(
                institution__contains='Birkbeck, Prifysgol Llundain',
            )
        )

    def test_preprint_author_queryset_get(self):
        self.assertTrue(
            repository_models.PreprintAuthor.objects.get(
                affiliation__contains='Birkbeck, Prifysgol Llundain',
            )
        )

    def test_account_queryset_filter(self):
        self.assertTrue(
            models.Account.objects.filter(
                first_name='Kathleen',
                last_name='Booth',
                email='ehqak6rxknzw35ih47oc@bbk.ac.uk',
                institution__contains='Birk',
                department__iendswith='numerical automation',
                country__code='GB',
            ).exists()
        )

    def test_frozen_author_queryset_filter(self):
        self.assertTrue(
            submission_models.FrozenAuthor.objects.filter(
                first_name='Kathleen',
                last_name='Booth',
                frozen_email='ehqak6rxknzw35ih47oc@bbk.ac.uk',
                institution__contains='Birk',
                department__iendswith='numerical automation',
                country__code='GB',
            ).exists()
        )

    def test_preprint_author_queryset_filter(self):
        self.assertTrue(
            repository_models.PreprintAuthor.objects.filter(
                preprint=self.preprint_one,
                account=self.kathleen_booth,
                affiliation__contains='Birkbeck',
            ).exists()
        )

    def test_account_queryset_update_or_create(self):
        kwargs = {
            'first_name': 'Michael',
            'last_name': 'Warner',
            'email': 'twlwpky6omkqdsc40zlm@example.org',
            'institution': 'Yale',
            'department': 'English',
            'country': self.country_us,
        }
        account, _created = models.Account.objects.update_or_create(
            **kwargs,
        )
        self.assertListEqual(
            list(kwargs.values()),
            [
                account.first_name,
                account.last_name,
                account.email,
                account.primary_affiliation().organization.custom_label.value,
                account.primary_affiliation().department,
                account.primary_affiliation().organization.locations.first().country,
            ]
        )

    def test_frozen_author_queryset_update_or_create_with_defaults(self):
        kwargs = {
            'first_name': 'Eric',
            'last_name': 'Hobsbawm',
        }
        defaults = {
            'institution': 'Yale',
            'department': 'English',
            'country': self.country_us,
        }
        frozen_author, _ = submission_models.FrozenAuthor.objects.update_or_create(
            defaults=defaults,
            **kwargs,
        )
        self.assertListEqual(
            list(kwargs.values()) + list(defaults.values()),
            [
                frozen_author.first_name,
                frozen_author.last_name,
                frozen_author.primary_affiliation().organization.custom_label.value,
                frozen_author.primary_affiliation().department,
                frozen_author.primary_affiliation().organization.locations.first().country,
            ]
        )

    def test_preprint_author_queryset_update_or_create_with_defaults(self):
        kwargs = {
            'account': self.e_hobsbawm,
            'preprint': self.preprint_one,
        }
        defaults = {
            'affiliation': 'Yale',
        }
        preprint_author, _ = repository_models.PreprintAuthor.objects.update_or_create(
            defaults=defaults,
            **kwargs,
        )
        self.assertEqual(self.e_hobsbawm, preprint_author.account)
        self.assertIn('Yale', preprint_author.affiliation)

    def test_account_queryset_update_or_create_with_defaults(self):
        kwargs = {
            'first_name': 'Eric',
            'last_name': 'Hobsbawm',
        }
        defaults = {
            'institution': 'Yale',
            'department': 'English',
            'country': self.country_us,
        }
        account, _created = models.Account.objects.update_or_create(
            defaults=defaults,
            **kwargs,
        )
        self.assertListEqual(
            list(kwargs.values()) + list(defaults.values()),
            [
                account.first_name,
                account.last_name,
                account.primary_affiliation().organization.custom_label.value,
                account.primary_affiliation().department,
                account.primary_affiliation().organization.locations.first().country,
            ]
        )

class TestOrganizationManagers(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.country_gb = models.Country.objects.create(
            code='GB',
            name='United Kingdom',
        )
        cls.location_uk_legacy = models.Location.objects.create(
            # Before integrating ROR we used country-wide locations
            # with no geonames ID or coordinates
            country=cls.country_gb,
        )
        cls.organization_turing_legacy = models.Organization.objects.create(
            # Before integrating ROR we used institution names with no ROR IDs
        )
        cls.organization_turing_legacy.locations.add(cls.location_uk_legacy)
        cls.name_turing_custom_legacy = models.OrganizationName.objects.create(
            value='The Alan Turing Institute',
            custom_label_for=cls.organization_turing_legacy,
        )
        cls.e_hobsbawm = helpers.create_user(
            'dp0dcbdgtzq4e7ml50fe@example.org',
            first_name='Eric',
            last_name='Hobsbawm',
        )
        cls.affiliation_historian = models.ControlledAffiliation.objects.create(
            account=cls.e_hobsbawm,
            title='Historian',
            organization=cls.organization_turing_legacy,
        )

        cls.ror_records = helpers.get_ror_records()

    def test_location_bulk_create_from_ror(self):
        models.Location.objects.bulk_create_from_ror(self.ror_records)
        for geonames_id in [2618425, 1835235, 2643743]:
            self.assertTrue(
                models.Location.objects.filter(geonames_id=geonames_id).exists()
            )

    def test_organization_bulk_create_from_ror(self):
        models.Location.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_create_from_ror(self.ror_records)
        for ror_id in ['00j1xwp39', '013yz9b19', '035dkdb55']:
            self.assertTrue(
                models.Organization.objects.filter(ror_id=ror_id).exists()
            )

    def test_organization_bulk_link_locations_from_ror_add(self):
        models.Location.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_link_locations_from_ror(
            self.ror_records
        )
        self.assertTrue(
            models.Organization.objects.filter(
                ror_id='00j1xwp39',
                locations__geonames_id=2618425,
            ).exists()
        )

    def test_organization_bulk_link_locations_from_ror_remove(self):
        # Set up data
        models.Location.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_link_locations_from_ror(
            self.ror_records
        )

        # Effectively remove a location while adding another
        self.ror_records[0]["locations"][0]["geonames_id"] = 123456789

        # Run test
        models.Location.objects.bulk_update_from_ror(self.ror_records)
        models.Organization.objects.bulk_link_locations_from_ror(
            self.ror_records
        )
        self.assertFalse(
            models.Organization.objects.filter(
                ror_id='00j1xwp39',
                locations__geonames_id=2618425,
            ).exists()
        )

    def test_organization_name_bulk_create_from_ror(self):
        models.Location.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_link_locations_from_ror(
            self.ror_records
        )
        models.OrganizationName.objects.bulk_create_from_ror(self.ror_records)
        for name in [
            'Korea Institute of Fusion Energy',
            'KFE',
            'Copenhagen School of Design and Technology',
            'KEA',
            'The Alan Turing Institute',
        ]:
            self.assertTrue(
                models.OrganizationName.objects.filter(value=name).exists()
            )
        self.assertTrue(
            models.Organization.objects.filter(
                ror_id='013yz9b19',
                acronyms__value='KFE',
            ).exists()
        )

    def test_location_bulk_update_from_ror_updates_existing_locations(self):
        # Set up data
        models.Location.objects.bulk_create_from_ror(self.ror_records)

        # Change one thing about the location but not its geonames_id
        self.ror_records[0]["locations"][0]["geonames_details"]["name"] = "Copenhagen 2"

        # Run test
        models.Location.objects.bulk_update_from_ror(self.ror_records)
        self.assertEqual(
            models.Location.objects.get(geonames_id=2618425).name,
            "Copenhagen 2"
        )

    def test_location_bulk_update_from_ror_adds_new_locations(self):
        """
        A ROR record that has already been imported into
        Janeway might contain a new location.
        In this case Location.bulk_update_from_ror should delegate that
        record to Location.bulk_create_from_ror.
        """
        # Set up data
        models.Location.objects.bulk_create_from_ror(self.ror_records)

        # Make the importer think it's a new location
        self.ror_records[0]["locations"][0]["geonames_id"] = 123456789
        self.ror_records[0]["locations"][0]["geonames_details"]["name"] = "Copenhagen 2"

        # Run test
        models.Location.objects.bulk_update_from_ror(self.ror_records)
        self.assertEqual(
            models.Location.objects.get(geonames_id=2618425).name,
            "Copenhagen"
        )
        self.assertEqual(
            models.Location.objects.get(geonames_id=123456789).name,
            "Copenhagen 2"
        )

    def test_organization_bulk_update_from_ror(self):
        # Set up data
        models.Location.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_create_from_ror(self.ror_records)

        # Change one thing about the organization but not its ROR id
        self.ror_records[0]["admin"]["last_modified"]["date"] = "2025-01-01"

        # Run test
        models.Location.objects.bulk_update_from_ror(self.ror_records)
        models.Organization.objects.bulk_update_from_ror(self.ror_records)
        self.assertEqual(
            models.Organization.objects.get(ror_id='00j1xwp39').ror_record_timestamp,
            "2025-01-01"
        )

    def test_organization_name_bulk_update_from_ror(self):
        # Set up data
        models.Location.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_link_locations_from_ror(
            self.ror_records,
        )
        models.OrganizationName.objects.bulk_create_from_ror(self.ror_records)

        # Change one thing about the organization name but not its ROR id
        self.ror_records[0]["names"][0]["value"] = "Copenhagen School of Design"

        # Run test
        models.Location.objects.bulk_update_from_ror(self.ror_records)
        models.Organization.objects.bulk_update_from_ror(self.ror_records)
        models.OrganizationName.objects.bulk_update_from_ror(self.ror_records)
        organization = models.Organization.objects.get(ror_id='00j1xwp39')
        self.assertEqual(
            organization.ror_display.value,
            "Copenhagen School of Design"
        )

    def test_organization_deduplicate_to_ror(self):
        # Set up ROR data
        models.Location.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_create_from_ror(self.ror_records)
        models.Organization.objects.bulk_link_locations_from_ror(
            self.ror_records
        )
        models.OrganizationName.objects.bulk_create_from_ror(self.ror_records)

        # Run test
        models.Organization.objects.all().deduplicate_to_ror()
        self.affiliation_historian.refresh_from_db()
        self.assertNotEqual(
            self.affiliation_historian.organization,
            self.organization_turing_legacy,
        )
        self.assertEqual(
            self.affiliation_historian.organization,
            models.Organization.objects.get(ror_id="035dkdb55"),
        )

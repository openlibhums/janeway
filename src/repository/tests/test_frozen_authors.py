from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from api import serializers as api_serializers
from core import models as core_models
from repository import logic as repository_logic, models as rm
from submission import models as sm
from utils.testing import helpers


class PreprintFrozenAuthorTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_roles(["author"])
        cls.press = helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        cls.manager = helpers.create_user("frozen_manager@janeway.systems")
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.manager],
            [],
        )
        cls.owner = helpers.create_user(
            "frozen_owner@janeway.systems",
            first_name="Olive",
            last_name="Owner",
        )
        cls.co_author_account = helpers.create_user(
            "frozen_co_author@janeway.systems",
            first_name="Coral",
            middle_name="B",
            last_name="Author",
        )
        for account in (cls.manager, cls.owner, cls.co_author_account):
            account.is_active = True
            account.save()
        helpers.create_affiliation(
            institution="Account Institute",
            account=cls.co_author_account,
        )
        cls.preprint = helpers.create_preprint(
            cls.repository,
            cls.owner,
            cls.subject,
        )
        cls.version_file = rm.PreprintFile.objects.create(
            preprint=cls.preprint,
            original_filename="version.pdf",
            mime_type="application/pdf",
        )
        cls.preprint.make_new_version(cls.version_file)

    def make_request(self, user=None):
        request = helpers.Request()
        request.user = user or self.manager
        request.repository = self.repository
        return request


class TestPreprintVersionAuthors(PreprintFrozenAuthorTestBase):
    def test_superseded_version_keeps_its_authors(self):
        old_version = self.preprint.current_version
        self.owner.biography = "Original biography"
        self.owner.save()
        self.preprint.make_new_version(self.version_file)
        old_version.refresh_from_db()

        working_author = self.preprint.frozen_authors().get(author=self.owner)
        working_author.last_name = "Renamed"
        working_author.save()
        self.owner.email = "changed@example.org"
        self.owner.biography = "New biography"
        self.owner.save()

        snapshot = old_version.authors.get()
        self.assertEqual(snapshot.full_name(), "Olive Owner")
        self.assertEqual(snapshot.email, "frozen_owner@janeway.systems")
        self.assertEqual(snapshot.biography, "Original biography")
        self.assertEqual(snapshot.institution, "Made Up University")
        self.assertFalse(snapshot.can_edit(self.manager))
        self.assertEqual(
            self.preprint.current_version.authors.get().full_name(),
            "Olive Renamed",
        )

    def test_deleting_current_version_restores_the_previous_one(self):
        old_version = self.preprint.current_version
        self.preprint.make_new_version(self.version_file)
        sm.FrozenAuthor.snapshot_account_for_preprint(
            self.co_author_account,
            self.preprint,
        )
        self.preprint.current_version.delete()
        old_version.refresh_from_db()
        self.assertFalse(old_version.metadata_frozen)
        self.assertEqual(
            [author.full_name() for author in self.preprint.frozen_authors()],
            ["Olive Owner"],
        )


class TestPreprintFrozenAuthorPermissions(PreprintFrozenAuthorTestBase):
    def test_who_can_edit_the_preprint_list(self):
        author = self.preprint.frozen_authors().get()
        self.assertTrue(author.can_edit(self.manager))
        self.assertFalse(author.can_edit(self.owner))
        self.assertFalse(author.can_edit(self.co_author_account))

        self.preprint.date_submitted = None
        self.preprint.save()
        co_author, _ = sm.FrozenAuthor.snapshot_account_for_preprint(
            self.co_author_account,
            self.preprint,
        )
        author.refresh_from_db()
        self.assertTrue(author.can_edit(self.owner))
        # As on journals: authors with accounts update their own profile.
        self.assertFalse(co_author.can_edit(self.owner))
        self.assertTrue(co_author.can_edit(self.co_author_account))

    def test_update_authors_editable_only_while_draft(self):
        update, _error = repository_logic.start_update(self.preprint, "version")
        author = update.frozenauthor_set.get()
        self.assertTrue(author.can_edit(self.owner))
        update.is_draft = False
        update.save()
        author.refresh_from_db()
        self.assertFalse(author.can_edit(self.owner))


@override_settings(URL_CONFIG="domain")
class TestPreprintAuthorPages(PreprintFrozenAuthorTestBase):
    """The journal-style author pages, for the submission author step."""

    def setUp(self):
        self.preprint.date_submitted = None
        self.preprint.save()
        self.client.force_login(self.owner)
        self.step_url = reverse("repository_authors", args=[self.preprint.pk])

    def post(self, url, data):
        return self.client.post(url, data, SERVER_NAME=self.repository.domain)

    def get(self, url):
        return self.client.get(url, SERVER_NAME=self.repository.domain)

    def names(self):
        return [author.full_name() for author in self.preprint.frozen_authors()]

    def test_search_adds_account_with_affiliations(self):
        self.post(
            self.step_url,
            {
                "search_authors": "",
                "author_search_text": "FROZEN_CO_AUTHOR@janeway.systems",
            },
        )
        co_author = self.preprint.frozen_authors().get(author=self.co_author_account)
        self.assertEqual(co_author.institution, "Account Institute")

    def test_manual_add_creates_no_account(self):
        accounts = core_models.Account.objects.count()
        self.post(
            self.step_url,
            {
                "add_author": "",
                "first_name": "No",
                "last_name": "Account",
                "frozen_email": "no_account@example.org",
            },
        )
        self.assertEqual(self.names(), ["Olive Owner", "No Account"])
        self.assertEqual(core_models.Account.objects.count(), accounts)

    def test_editing_own_author_record_does_not_change_account(self):
        author = self.preprint.frozen_authors().get(author=self.owner)
        self.post(
            reverse("repository_edit_author", args=[self.preprint.pk, author.pk]),
            {
                "save_author": author.pk,
                "first_name": "Olivia",
                "last_name": "Owner-Smith",
            },
        )
        author.refresh_from_db()
        self.owner.refresh_from_db()
        self.assertEqual(author.full_name(), "Olivia Owner-Smith")
        self.assertEqual(
            (self.owner.first_name, self.owner.last_name), ("Olive", "Owner")
        )

    def test_add_ror_affiliation(self):
        organization = core_models.Organization.objects.create(ror_id="test0001")
        core_models.OrganizationName.objects.create(
            value="ROR Test University",
            ror_display_for=organization,
            label_for=organization,
        )
        author = self.preprint.frozen_authors().get(author=self.owner)
        search = self.get(
            reverse(
                "repository_organization_search",
                args=[self.preprint.pk, author.pk],
            )
            + "?q=ROR"
        )
        self.assertContains(search, "ROR Test University")
        self.post(
            reverse(
                "repository_affiliation_create",
                args=[self.preprint.pk, author.pk, organization.pk],
            ),
            {"is_primary": "True", "department": "Testing"},
        )
        self.assertTrue(
            author.affiliations.filter(
                organization=organization, department="Testing"
            ).exists()
        )

    def test_warns_about_authors_without_affiliations(self):
        no_affiliation = sm.FrozenAuthor.objects.create(
            preprint=self.preprint,
            first_name="No",
            last_name="Affiliation",
            order=5,
        )
        response = self.get(self.step_url)
        self.assertContains(response, "data-missing-affiliations")
        self.assertContains(
            response,
            reverse(
                "repository_organization_search",
                args=[self.preprint.pk, no_affiliation.pk],
            ),
        )
        # The owner has an affiliation, so is not listed.
        self.assertEqual(
            [author for author, _ in response.context["authors_without_affiliations"]],
            [no_affiliation],
        )

    def test_cannot_open_linked_co_author(self):
        co_author, _ = sm.FrozenAuthor.snapshot_account_for_preprint(
            self.co_author_account,
            self.preprint,
        )
        response = self.get(
            reverse("repository_edit_author", args=[self.preprint.pk, co_author.pk])
        )
        self.assertEqual(response.status_code, 404)


class TestPreprintAuthorsToArticle(PreprintFrozenAuthorTestBase):
    @mock.patch("repository.models.files.copy_preprint_file_to_article")
    def test_create_article_copies_authors(self, _copy_file):
        co_author, _ = sm.FrozenAuthor.snapshot_account_for_preprint(
            self.co_author_account,
            self.preprint,
        )
        co_author.add_credit("writing-original-draft")
        section = sm.Section.objects.filter(journal=self.journal).first()

        article = self.preprint.create_article(
            self.journal,
            "Unassigned",
            None,
            section,
        )

        article_authors = sm.FrozenAuthor.objects.filter(article=article)
        self.assertEqual(
            [author.full_name() for author in article_authors],
            ["Olive Owner", "Coral B Author"],
        )
        copied = article_authors.get(author=self.co_author_account)
        self.assertEqual(copied.institution, "Account Institute")
        self.assertEqual(
            [credit.role for credit in copied.credits],
            ["writing-original-draft"],
        )
        self.assertIsNone(copied.preprint)
        self.assertEqual(self.preprint.frozen_authors().count(), 2)


class TestPreprintAuthorsAPI(PreprintFrozenAuthorTestBase):
    def test_serialized_author_keeps_field_names(self):
        data = api_serializers.PreprintSerializer(self.preprint).data["authors"]
        self.assertEqual(
            set(data[0]),
            {
                "pk",
                "email",
                "first_name",
                "middle_name",
                "last_name",
                "salutation",
                "suffix",
                "orcid",
                "institution",
            },
        )
        self.assertEqual(data[0]["pk"], self.owner.pk)

    def test_replace_matches_authors_and_respects_who_can_edit(self):
        self.preprint.date_submitted = None
        self.preprint.save()
        no_email = sm.FrozenAuthor.objects.create(
            preprint=self.preprint,
            first_name="No",
            last_name="Email",
            order=1,
        )
        co_author, _ = sm.FrozenAuthor.snapshot_account_for_preprint(
            self.co_author_account,
            self.preprint,
        )
        co_author.add_credit("writing-original-draft")
        accounts = core_models.Account.objects.count()
        author_list = repository_logic.PreprintAuthorList(self.preprint)
        owner_pk = author_list.authors().get(author=self.owner).pk
        author_list.replace(
            [
                {
                    "email": "new.author@example.org",
                    "first_name": "New",
                    "last_name": "Author",
                    "institution": "API University",
                },
                # A new email: matched by name, as they have no account.
                {
                    "email": "no.email@example.org",
                    "first_name": "No",
                    "last_name": "Email",
                },
                {
                    "email": "frozen_owner@janeway.systems",
                    "first_name": "Olive",
                    "last_name": "Renamed",
                },
                {
                    "email": "frozen_co_author@janeway.systems",
                    "first_name": "Coral",
                    "last_name": "Renamed",
                    "institution": "Not Coral's Institute",
                },
            ],
            editor=self.owner,
        )
        self.assertEqual(
            [author.full_name() for author in author_list.authors()],
            ["New Author", "No Email", "Olive Renamed", "Coral B Author"],
        )
        self.assertEqual(author_list.authors().get(author=self.owner).pk, owner_pk)
        self.assertTrue(author_list.authors().filter(pk=no_email.pk).exists())
        # The owner cannot change a co-author who has an account.
        co_author.refresh_from_db()
        self.assertEqual(co_author.institution, "Account Institute")
        self.assertEqual(
            [c.role for c in co_author.credits], ["writing-original-draft"]
        )
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.last_name, "Owner")
        self.assertEqual(core_models.Account.objects.count(), accounts)


class TestPreprintAuthorDataRules(PreprintFrozenAuthorTestBase):
    def test_adding_account_adopts_unlinked_entry_with_same_email(self):
        unlinked = sm.FrozenAuthor.objects.create(
            preprint=self.preprint,
            first_name="Coral",
            last_name="Author",
            frozen_email="FROZEN_CO_AUTHOR@janeway.systems",
            order=5,
        )
        frozen_author, created = sm.FrozenAuthor.snapshot_account_for_preprint(
            self.co_author_account,
            self.preprint,
        )
        self.assertFalse(created)
        self.assertEqual(frozen_author.pk, unlinked.pk)
        self.assertEqual(frozen_author.author, self.co_author_account)
        self.assertEqual(self.preprint.frozen_authors().count(), 2)

    def test_editing_row_into_another_person_unlinks_the_account(self):
        author = self.preprint.frozen_authors().get(author=self.owner)
        repository_logic.set_author_contact_details(
            author,
            "bob@example.org",
            None,
            names_changed=True,
        )
        author.save()
        self.assertIsNone(author.author)
        self.assertEqual(author.email, "bob@example.org")

    def test_email_of_another_account_relinks(self):
        author = self.preprint.frozen_authors().get(author=self.owner)
        repository_logic.set_author_contact_details(
            author,
            "frozen_co_author@janeway.systems",
            None,
            names_changed=True,
        )
        author.save()
        self.assertEqual(author.author, self.co_author_account)

    def test_account_merge_does_not_list_someone_twice(self):
        sm.FrozenAuthor.snapshot_account_for_preprint(
            self.co_author_account,
            self.preprint,
        )
        repository_logic.resolve_account_merge(self.co_author_account, self.owner)
        self.assertFalse(
            self.preprint.frozen_authors()
            .filter(author=self.co_author_account)
            .exists()
        )
        self.assertTrue(
            self.preprint.frozen_authors().filter(author=self.owner).exists()
        )

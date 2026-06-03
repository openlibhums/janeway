__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase
from django.urls import reverse

from screening import models as screening_models
from utils.testing import helpers


class ScreeningFormsManagerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "forms-manager-editor@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.author = helpers.create_user(
            "forms-manager-author@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        cls.author.is_active = True
        cls.author.save()
        cls.screening_form = screening_models.ScreeningForm.objects.create(
            journal=cls.journal_one,
            name="ILR Default",
            intro="Welcome",
            thanks="Thanks",
        )

    def test_screening_forms_list_renders_for_editor(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("screening_forms"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ILR Default")

    def test_screening_forms_list_blocks_non_editor(self):
        self.client.force_login(self.author)
        response = self.client.get(
            reverse("screening_forms"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertNotEqual(response.status_code, 200)

    def test_create_screening_form(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse("screening_forms"),
            {
                "name": "Internal Review Form",
                "intro": "<p>Please read carefully.</p>",
                "thanks": "<p>Thank you.</p>",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertTrue(
            screening_models.ScreeningForm.objects.filter(
                journal=self.journal_one,
                name="Internal Review Form",
            ).exists()
        )

    def test_soft_delete_screening_form(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse("screening_forms"),
            {"delete": str(self.screening_form.pk)},
            SERVER_NAME=self.journal_one.domain,
        )
        self.screening_form.refresh_from_db()
        self.assertTrue(self.screening_form.deleted)

    def test_edit_screening_form_metadata(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse("edit_screening_form", kwargs={"form_id": self.screening_form.pk}),
            {
                "screening_form": "1",
                "name": "Renamed Form",
                "intro": "Updated intro",
                "thanks": "Updated thanks",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.screening_form.refresh_from_db()
        self.assertEqual(self.screening_form.name, "Renamed Form")

    def test_add_element_to_form(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse("edit_screening_form", kwargs={"form_id": self.screening_form.pk}),
            {
                "element": "1",
                "name": "Recommendation Notes",
                "kind": "textarea",
                "required": "on",
                "order": "1",
                "default_visibility": "on",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.screening_form.refresh_from_db()
        self.assertEqual(self.screening_form.elements.count(), 1)
        self.assertEqual(
            self.screening_form.elements.first().name,
            "Recommendation Notes",
        )

    def test_delete_element_from_form(self):
        element = screening_models.ScreeningFormElement.objects.create(
            name="Temp Element",
            kind="text",
            required=False,
            order=2,
        )
        self.screening_form.elements.add(element)
        self.client.force_login(self.editor)
        self.client.post(
            reverse("edit_screening_form", kwargs={"form_id": self.screening_form.pk}),
            {"delete": str(element.pk)},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertFalse(
            screening_models.ScreeningFormElement.objects.filter(pk=element.pk).exists()
        )

    def test_edit_element_via_element_url(self):
        element = screening_models.ScreeningFormElement.objects.create(
            name="Old Name",
            kind="text",
            required=False,
            order=3,
        )
        self.screening_form.elements.add(element)
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "edit_screening_form_element",
                kwargs={"form_id": self.screening_form.pk, "element_id": element.pk},
            ),
            {
                "element": "1",
                "name": "Renamed Element",
                "kind": "text",
                "order": "3",
                "default_visibility": "on",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        element.refresh_from_db()
        self.assertEqual(element.name, "Renamed Element")

    def test_cross_journal_element_lookup_is_404(self):
        """An element belonging to journal_two's form must not be loadable
        via journal_one's edit_screening_form URL even if its pk is known."""
        other_form = screening_models.ScreeningForm.objects.create(
            journal=self.journal_two,
            name="Other Journal Form",
        )
        other_element = screening_models.ScreeningFormElement.objects.create(
            name="Foreign Element",
            kind="text",
            required=False,
            order=1,
        )
        other_form.elements.add(other_element)

        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "edit_screening_form_element",
                kwargs={
                    "form_id": self.screening_form.pk,
                    "element_id": other_element.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)

    def test_cross_journal_element_delete_is_404(self):
        """Posting a delete for an element on another journal's form must
        not delete it via journal_one's URL."""
        other_form = screening_models.ScreeningForm.objects.create(
            journal=self.journal_two,
            name="Other Journal Form 2",
        )
        other_element = screening_models.ScreeningFormElement.objects.create(
            name="Foreign Element 2",
            kind="text",
            required=False,
            order=1,
        )
        other_form.elements.add(other_element)

        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("edit_screening_form", kwargs={"form_id": self.screening_form.pk}),
            {"delete": str(other_element.pk)},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            screening_models.ScreeningFormElement.objects.filter(
                pk=other_element.pk
            ).exists()
        )

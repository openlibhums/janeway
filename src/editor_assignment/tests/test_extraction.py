__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase
from django.urls import reverse


class EditorAssignmentExtractionTests(TestCase):
    """Confirms that moving editor-assignment views and logic into the
    editor_assignment app does not break the public surface.

    See bau#271.
    """

    def test_review_views_shim_resolves_moved_view_callables(self):
        from review import views

        # The shim re-exports the decorated callables; assert each name resolves.
        for name in (
            "unassigned",
            "unassigned_article",
            "assign_editor",
            "assign_editor_move_to_review",
            "unassign_editor",
            "assignment_notification",
            "move_to_review",
        ):
            self.assertTrue(
                hasattr(views, name),
                msg="review.views must re-export {}".format(name),
            )

    def test_review_logic_shim_resolves_moved_helpers(self):
        from review import logic

        for name in (
            "assign_editor",
            "get_assignment_context",
            "get_unassignment_context",
        ):
            self.assertTrue(
                hasattr(logic, name),
                msg="review.logic must re-export {}".format(name),
            )

    def test_editor_assignment_views_are_importable_directly(self):
        from editor_assignment import views

        for name in (
            "unassigned",
            "unassigned_article",
            "assign_editor",
            "assign_editor_move_to_review",
            "unassign_editor",
            "assignment_notification",
            "move_to_review",
        ):
            self.assertTrue(hasattr(views, name))

    def test_editor_assignment_logic_helpers_are_importable_directly(self):
        from editor_assignment import logic

        for name in (
            "assign_editor",
            "get_assignment_context",
            "get_unassignment_context",
        ):
            self.assertTrue(hasattr(logic, name))

    def test_review_unassigned_url_name_still_resolves(self):
        # Legacy URL name and path remain available for backward compatibility.
        path = reverse("review_unassigned")
        self.assertIn("/review/unassigned/", path)

    def test_review_unassigned_article_url_name_still_resolves(self):
        path = reverse("review_unassigned_article", kwargs={"article_id": 1})
        self.assertIn("/review/unassigned/article/1/", path)

    def test_editor_assignment_list_is_primary_url(self):
        path = reverse("editor_assignment_list")
        self.assertIn("/editor-assignment/", path)

    def test_editor_assignment_article_is_primary_url(self):
        path = reverse("editor_assignment_article", kwargs={"article_id": 1})
        self.assertIn("/editor-assignment/article/1/", path)

    def test_all_primary_url_names_resolve(self):
        for name, kwargs in (
            ("editor_assignment_list", {}),
            ("editor_assignment_article", {"article_id": 1}),
            (
                "editor_assignment_assign",
                {"article_id": 1, "editor_id": 2, "assignment_type": "editor"},
            ),
            (
                "editor_assignment_assign_and_move",
                {"article_id": 1, "editor_id": 2, "assignment_type": "editor"},
            ),
            ("editor_assignment_unassign", {"article_id": 1, "editor_id": 2}),
            ("editor_assignment_notification", {"article_id": 1, "editor_id": 2}),
            ("editor_assignment_move_to_review", {"article_id": 1}),
        ):
            self.assertIn(
                "/editor-assignment/",
                reverse(name, kwargs=kwargs),
                msg="Primary URL {} must mount under /editor-assignment/".format(
                    name,
                ),
            )

    def test_core_workflow_can_import_assign_editor_from_review_logic(self):
        # core.workflow uses `from review.logic import assign_editor` —
        # this must continue to resolve to the moved callable.
        from review.logic import assign_editor as review_assign_editor
        from editor_assignment.logic import assign_editor as new_assign_editor

        self.assertIs(review_assign_editor, new_assign_editor)

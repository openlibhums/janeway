__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from django.urls import reverse

from events import logic as event_logic
from review import models
from screening import logic as screening_logic
from screening.models import ScreeningRound


def setup_after_editor_assignment(article, next_element):
    """Idempotent per-stage setup when an article enters the next workflow
    element following editor assignment. New downstream stages should add
    their initialisation here (or, when there are enough of them, this
    should become a registry).
    """
    if next_element.element_name == "review":
        models.ReviewRound.objects.get_or_create(article=article, round_number=1)
    elif next_element.element_name == "screening":
        if not ScreeningRound.objects.filter(article=article).exists():
            screening_logic.open_screening_round(article)


def get_assignment_context(request, article, editor, assignment):
    review_in_review_url = request.journal.site_url(
        reverse("review_in_review", kwargs={"article_id": article.pk})
    )
    email_context = {
        "article": article,
        "editor": editor,
        "assignment": assignment,
        "review_in_review_url": review_in_review_url,
    }

    return email_context


def get_unassignment_context(request, assignment):
    email_context = {
        "article": assignment.article,
        "assignment": assignment,
        "editor": request.user,
    }

    return email_context


def assign_editor(
    article,
    editor,
    assignment_type,
    request=None,
    skip=True,
    automate_email=False,
):
    from core.forms import SettingEmailForm

    assignment, created = models.EditorAssignment.objects.get_or_create(
        article=article,
        editor=editor,
        editor_type=assignment_type,
    )
    if request and created and automate_email:
        email_context = get_assignment_context(
            request,
            article,
            editor,
            assignment,
        )
        form = SettingEmailForm(
            setting_name="editor_assignment",
            email_context=email_context,
            request=request,
        )
        post_data = {
            "subject": form.fields["subject"].initial,
            "body": form.fields["body"].initial,
        }
        form = SettingEmailForm(
            post_data,
            setting_name="editor_assignment",
            email_context=email_context,
            request=request,
        )

        if form.is_valid():
            kwargs = {
                "email_data": form.as_dataclass(),
                "editor_assignment": assignment,
                "request": request,
                "skip": skip,
                "acknowledgement": False,
            }
            event_logic.Events.raise_event(
                event_logic.Events.ON_ARTICLE_ASSIGNED,
                task_object=article,
                **kwargs,
            )
            if not skip:
                event_logic.Events.raise_event(
                    event_logic.Events.ON_ARTICLE_ASSIGNED_ACKNOWLEDGE,
                    **kwargs,
                )
    return assignment, created

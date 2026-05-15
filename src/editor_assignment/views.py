__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core import (
    forms as core_forms,
    logic as core_logic,
    models as core_models,
)
from editor_assignment import logic
from events import logic as event_logic
from review import models
from security.decorators import (
    any_editor_user_required,
    editor_user_required,
    senior_editor_user_required,
)
from submission import models as submission_models
from utils import ithenticate, models as util_models


@any_editor_user_required
def unassigned(request):
    """
    Displays a list of unassigned articles.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    articles = submission_models.Article.objects.filter(
        stage=submission_models.STAGE_UNASSIGNED, journal=request.journal
    )

    if not request.user.is_editor(request) and request.user.is_section_editor(request):
        articles = core_logic.filter_articles_to_editor_assigned(request, articles)

    template = "review/unassigned.html"
    context = {
        "articles": articles,
    }

    return render(request, template, context)


@editor_user_required
def unassigned_article(request, article_id):
    """
    Displays metadata of an individual article, can send details to Crosscheck for reporting.
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse or Redirect if POST
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    if article.ithenticate_id and not article.ithenticate_score:
        ithenticate.fetch_percentage(request.journal, [article])

    if "crosscheck" in request.POST:
        file_id = request.POST.get("crosscheck")
        file = get_object_or_404(core_models.File, pk=file_id)
        try:
            id = ithenticate.send_to_ithenticate(article, file)
            article.ithenticate_id = id
            article.save()
        except AssertionError:
            messages.add_message(
                request,
                messages.ERROR,
                "Error returned by iThenticate. Check login details and API status.",
            )

        return redirect(
            reverse(
                "review_unassigned_article",
                kwargs={"article_id": article.pk},
            )
        )

    current_editors = [
        assignment.editor.pk
        for assignment in models.EditorAssignment.objects.filter(article=article)
    ]
    editors = core_models.AccountRole.objects.filter(
        role__slug="editor", journal=request.journal
    ).exclude(user__id__in=current_editors)
    section_editors = core_models.AccountRole.objects.filter(
        role__slug="section-editor", journal=request.journal
    ).exclude(user__id__in=current_editors)

    template = "review/unassigned_article.html"
    context = {
        "article": article,
        "editors": editors,
        "section_editors": section_editors,
        "next_workflow_element": _next_workflow_element(request.journal),
    }

    return render(request, template, context)


@senior_editor_user_required
def assign_editor_move_to_review(request, article_id, editor_id, assignment_type):
    """Allows an editor to assign another editor to an article and moves to review."""
    assign_editor(
        request, article_id, editor_id, assignment_type, should_redirect=False
    )
    return move_to_review(request, article_id)


@senior_editor_user_required
def assign_editor(
    request, article_id, editor_id, assignment_type, should_redirect=True
):
    """
    Allows a Senior Editor to assign another editor to an article.
    :param request: HttpRequest object
    :param article_id: Article PK
    :param editor_id: Account PK
    :param assignment_type: string, 'section-editor' or 'editor'
    :param should_redirect: if true, we redirect the user to the notification page
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    editor = get_object_or_404(core_models.Account, pk=editor_id)

    if not editor.has_an_editor_role(request):
        messages.add_message(
            request, messages.WARNING, "User is not an Editor or Section Editor"
        )
        return redirect(
            reverse("review_unassigned_article", kwargs={"article_id": article.pk})
        )

    _, created = logic.assign_editor(article, editor, assignment_type, request)
    messages.add_message(
        request, messages.SUCCESS, "{0} added as an Editor".format(editor.full_name())
    )
    if created and should_redirect:
        return redirect(
            "{0}?return={1}".format(
                reverse(
                    "review_assignment_notification",
                    kwargs={"article_id": article_id, "editor_id": editor.pk},
                ),
                request.GET.get("return"),
            )
        )
    elif not created:
        messages.add_message(
            request,
            messages.WARNING,
            "{0} is already an Editor on this article.".format(editor.full_name()),
        )
    if should_redirect:
        return redirect(
            reverse("review_unassigned_article", kwargs={"article_id": article_id})
        )


@senior_editor_user_required
def unassign_editor(request, article_id, editor_id):
    """Unassigns an editor from an article"""
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    editor = get_object_or_404(core_models.Account, pk=editor_id)
    assignment = get_object_or_404(
        models.EditorAssignment, article=article, editor=editor
    )
    skip = request.POST.get("skip")
    email_context = logic.get_unassignment_context(request, assignment)
    form = core_forms.SettingEmailForm(
        setting_name="unassign_editor",
        email_context=email_context,
        request=request,
    )

    if request.method == "POST":
        form = core_forms.SettingEmailForm(
            request.POST,
            request.FILES,
            setting_name="unassign_editor",
            email_context=email_context,
            request=request,
        )

        if form.is_valid() or skip:
            kwargs = {
                "email_data": form.as_dataclass(),
                "assignment": assignment,
                "request": request,
                "skip": skip,
            }

            event_logic.Events.raise_event(
                event_logic.Events.ON_ARTICLE_UNASSIGNED, **kwargs
            )

            assignment.delete()

            util_models.LogEntry.add_entry(
                types="EditorialAction",
                description="Editor {0} unassigned from article {1}".format(
                    editor.full_name(), article.id
                ),
                level="Info",
                request=request,
                target=article,
            )

            return redirect(
                reverse("review_unassigned_article", kwargs={"article_id": article_id})
            )

    template = "review/unassign_editor.html"
    context = {
        "article": article,
        "assignment": assignment,
        "form": form,
    }

    return render(request, template, context)


@senior_editor_user_required
def assignment_notification(request, article_id, editor_id):
    """
    A senior editor can sent a notification to an assigned editor.
    :param request: HttpRequest object
    :param article_id: Article PK
    :param editor_id: Account PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    editor = get_object_or_404(core_models.Account, pk=editor_id)
    assignment = get_object_or_404(
        models.EditorAssignment, article=article, editor=editor, notified=False
    )

    email_context = logic.get_assignment_context(request, article, editor, assignment)

    form = core_forms.SettingEmailForm(
        setting_name="editor_assignment",
        email_context=email_context,
        request=request,
    )

    if request.POST:
        form = core_forms.SettingEmailForm(
            request.POST,
            request.FILES,
            setting_name="editor_assignment",
            email_context=email_context,
            request=request,
        )
        skip = request.POST.get("skip")
        form_valid = form.is_valid()
        if skip or form_valid:
            kwargs = {
                "editor_assignment": assignment,
                "request": request,
                "skip": skip,
                "email_data": form.as_dataclass(),
            }

            event_logic.Events.raise_event(
                event_logic.Events.ON_EDITOR_MANUALLY_ASSIGNED, **kwargs
            )

            assignment.notified = True
            assignment.save()

            if request.GET.get("return", None):
                return redirect(request.GET.get("return"))
            else:
                return redirect(
                    reverse(
                        "review_unassigned_article", kwargs={"article_id": article_id}
                    )
                )

    template = "review/assignment_notification.html"
    context = {
        "article": article,
        "editor": editor,
        "assignment": assignment,
        "form": form,
    }

    return render(request, template, context)


def _next_workflow_element(journal):
    """Compatibility shim. Prefer core.workflow.get_next_workflow_element."""
    from core import workflow as core_workflow

    return core_workflow.get_next_workflow_element(journal, "editor_assignment")


def _setup_next_stage(article, next_element):
    """Idempotent per-stage setup when an article enters the next workflow
    element. New downstream stages should add their initialisation here
    (or, when there are enough of them, this should become a registry).
    """
    if next_element.element_name == "review":
        models.ReviewRound.objects.get_or_create(article=article, round_number=1)
    elif next_element.element_name == "screening":
        from screening import logic as screening_logic

        if not screening_logic.screening_models.ScreeningRound.objects.filter(
            article=article,
        ).exists():
            screening_logic.open_screening_round(article)


@editor_user_required
def move_to_next_stage(request, article_id, should_redirect=True):
    """Move an article out of editor assignment into whichever workflow
    element follows it for this journal.

    Replaces the old hardcoded move_to_review action so that journals with
    a Screening element get routed to Screening, and any future workflow
    element inserted after Editor Assignment is honoured automatically.
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    if article.editorassignment_set.all().count() == 0:
        messages.add_message(
            request,
            messages.INFO,
            "You must assign an editor before moving the article on.",
        )
        if should_redirect:
            return redirect(
                reverse("review_unassigned_article", kwargs={"article_id": article_id})
            )
        return

    next_element = _next_workflow_element(request.journal)
    if next_element is None:
        messages.add_message(
            request,
            messages.WARNING,
            "There is no next workflow element configured for this journal.",
        )
        if should_redirect:
            return redirect(
                reverse("review_unassigned_article", kwargs={"article_id": article_id})
            )
        return

    # Pre-create the next stage's artefacts (Round 1, etc.) so they exist
    # when the user lands on the next page.
    _setup_next_stage(article, next_element)

    # Delegate the stage transition, log entry, and redirect to the
    # canonical core.workflow machinery.
    from core import workflow as core_workflow

    workflow = request.journal.workflow()
    current_element = workflow.elements.get(element_name="editor_assignment")
    response = core_workflow.workflow_next(
        handshake_url=current_element.handshake_url,
        request=request,
        article=article,
        switch_stage=True,
    )
    if response and should_redirect:
        if request.GET.get("return", None):
            return redirect(request.GET.get("return"))
        return response
    if should_redirect:
        return redirect(reverse("core_dashboard"))


# Backward-compat alias for code/URLs that still reference the original
# move_to_review name.
move_to_review = move_to_next_stage

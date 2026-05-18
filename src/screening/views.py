__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core import forms as core_forms
from core import workflow as core_workflow
from events import logic as event_logic
from screening import forms, logic, models as screening_models
from screening.decorators import (
    screener_for_assignment_required,
    screener_or_editor_for_assignment_required,
)
from security.decorators import (
    any_editor_user_required,
    editor_user_required,
    senior_editor_user_required,
)
from submission import models as submission_models


def journal_has_screening_element(journal):
    return journal.element_in_workflow("screening")


@any_editor_user_required
def screening_list(request):
    """List articles currently in the screening stage for this journal."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    articles = submission_models.Article.objects.filter(
        stage=submission_models.STAGE_SCREENING,
        journal=request.journal,
    ).select_related("correspondence_author", "section")

    template = "admin/screening/list.html"
    context = {"articles": articles}
    return render(request, template, context)


@editor_user_required
def screening_article(request, article_id):
    """Per-article screening dashboard.

    Shows every screening round on the article, the assignments on each
    round, and editor-facing actions for opening a new round or inviting
    a screener to the latest round.
    """
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    is_screening_stage = article.stage == submission_models.STAGE_SCREENING

    rounds = (
        screening_models.ScreeningRound.objects.filter(article=article)
        .prefetch_related("screeningassignment_set__screener")
        .order_by("round_number")
    )
    latest_round = rounds.last() if rounds.exists() else None
    next_workflow_element = core_workflow.get_next_workflow_element(
        request.journal,
        "screening",
    )
    checklist = logic.ensure_checklist_for_article(article)
    checklist_templates = screening_models.TechnicalChecklistTemplate.objects.filter(
        journal=request.journal,
        deleted=False,
    )

    revision_requests = screening_models.ScreeningRevisionRequest.objects.filter(
        article=article,
    ).order_by("-date_requested")

    template = "admin/screening/article.html"
    context = {
        "article": article,
        "rounds": rounds,
        "latest_round": latest_round,
        "next_workflow_element": next_workflow_element,
        "checklist": checklist,
        "checklist_templates": checklist_templates,
        "is_screening_stage": is_screening_stage,
        "revision_requests": revision_requests,
    }
    return render(request, template, context)


@editor_user_required
def add_screening_round(request, article_id):
    """Open a new screening round on an article.

    Idempotent on GET — round opening is POST-only. If no rounds exist
    yet, this is the first round; otherwise it is one higher than the
    most recent.
    """
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )

    if request.method != "POST":
        return redirect(reverse("screening_article", kwargs={"article_id": article.pk}))

    new_round = logic.open_screening_round(article)
    messages.add_message(
        request,
        messages.SUCCESS,
        "Screening round {0} opened.".format(new_round.round_number),
    )
    return redirect(reverse("screening_article", kwargs={"article_id": article.pk}))


@editor_user_required
def add_screening_assignment(request, article_id, round_id):
    """Invite a screener to a specific screening round.

    The screener choice list is restricted to the journal's editorial
    team and excludes anyone already invited to this round.
    """
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    screening_round = get_object_or_404(
        screening_models.ScreeningRound,
        pk=round_id,
        article=article,
    )

    form = forms.ScreeningAssignmentForm(
        request.POST or None,
        article=article,
        journal=request.journal,
        screening_round=screening_round,
        editor=request.user,
    )

    if request.method == "POST" and form.is_valid():
        assignment = form.save()
        return redirect(
            reverse(
                "screening_assignment_notification",
                kwargs={
                    "article_id": article.pk,
                    "assignment_id": assignment.pk,
                },
            )
        )

    candidates = logic.annotate_candidate_screeners(
        form.fields["screener"].queryset,
        journal=request.journal,
    )

    pool = screening_models.ScreeningPool.objects.filter(
        journal=request.journal,
    ).first()
    pool_groups = list(pool.groups.all()) if pool else []

    template = "admin/screening/add_assignment.html"
    context = {
        "article": article,
        "screening_round": screening_round,
        "form": form,
        "candidates": candidates,
        "pool_groups": pool_groups,
    }
    return render(request, template, context)


@editor_user_required
def screening_assignment_notification(request, article_id, assignment_id):
    """Preview and edit the invitation email before sending it to the
    screener. Mirrors the editor_assignment / review notification
    flow. POST sends the email (or skips it) and raises
    ON_SCREENER_REQUESTED with the edited email body."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    assignment = get_object_or_404(
        screening_models.ScreeningAssignment,
        pk=assignment_id,
        article=article,
    )

    screening_requests_url = request.journal.site_url(
        reverse("screening_requests"),
    )
    email_context = {
        "article": article,
        "screening_assignment": assignment,
        "screening_requests_url": screening_requests_url,
    }
    form = core_forms.SettingEmailForm(
        setting_name="screening_invitation",
        email_context=email_context,
        request=request,
    )

    if request.method == "POST":
        form = core_forms.SettingEmailForm(
            request.POST,
            request.FILES,
            setting_name="screening_invitation",
            email_context=email_context,
            request=request,
        )
        skip = request.POST.get("skip")
        if skip or form.is_valid():
            event_logic.Events.raise_event(
                event_logic.Events.ON_SCREENER_REQUESTED,
                task_object=article,
                request=request,
                screening_assignment=assignment,
                email_data=form.as_dataclass() if not skip else None,
                skip=bool(skip),
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                (
                    "{} invited as a screener (notification skipped).".format(
                        assignment.screener.full_name(),
                    )
                    if skip
                    else "{} invited as a screener and notified.".format(
                        assignment.screener.full_name(),
                    )
                ),
            )
            return redirect(
                reverse("screening_article", kwargs={"article_id": article.pk})
            )

    template = "admin/screening/assignment_notification.html"
    context = {
        "article": article,
        "assignment": assignment,
        "form": form,
    }
    return render(request, template, context)


@editor_user_required
def edit_screening_assignment(request, article_id, assignment_id):
    """Allow an editor to amend an open screening assignment — change
    due date, anonymity flags, form, or the screener identity."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    assignment = get_object_or_404(
        screening_models.ScreeningAssignment,
        pk=assignment_id,
        article=article,
    )
    if assignment.is_withdrawn:
        messages.add_message(
            request,
            messages.WARNING,
            "Withdrawn assignments cannot be edited. Reset the assignment first.",
        )
        return redirect(
            reverse("screening_article", kwargs={"article_id": article.pk}),
        )
    form = forms.ScreeningAssignmentForm(
        request.POST or None,
        instance=assignment,
        article=article,
        journal=request.journal,
        screening_round=assignment.screening_round,
        editor=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Screening assignment updated.",
        )
        return redirect(
            reverse("screening_article", kwargs={"article_id": article.pk}),
        )

    template = "admin/screening/edit_assignment.html"
    context = {
        "article": article,
        "screening_round": assignment.screening_round,
        "assignment": assignment,
        "form": form,
    }
    return render(request, template, context)


@editor_user_required
@require_POST
def withdraw_screening_assignment(request, article_id, assignment_id):
    """Withdraw an open screening assignment — sets it to the withdrawn
    state so the screener can no longer act on it. Idempotent."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    assignment = get_object_or_404(
        screening_models.ScreeningAssignment,
        pk=assignment_id,
        article=article,
    )
    if assignment.withdraw():
        event_logic.Events.raise_event(
            event_logic.Events.ON_SCREENING_WITHDRAWN,
            task_object=article,
            request=request,
            screening_assignment=assignment,
        )
    messages.add_message(
        request,
        messages.SUCCESS,
        "Screening assignment withdrawn.",
    )
    return redirect(
        reverse("screening_article", kwargs={"article_id": article.pk}),
    )


@editor_user_required
def view_screening_report(request, article_id, assignment_id):
    """Editor-facing read-only view of a completed screening report.

    Shows the screener's identity, recommendation, comments for the
    editor, suggested reviewers (if any), and each form answer
    submitted on the screening form.
    """
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    assignment = get_object_or_404(
        screening_models.ScreeningAssignment,
        pk=assignment_id,
        article=article,
    )
    answers = assignment.screening_form_answers()

    template = "admin/screening/view_report.html"
    context = {
        "article": article,
        "assignment": assignment,
        "answers": answers,
        "back_url": logic.back_url_for_assignment(request, assignment),
    }
    return render(request, template, context)


@editor_user_required
@require_POST
def reset_screening_assignment(request, article_id, assignment_id):
    """Reset a completed screening assignment back to the in-progress
    state so the screener can revise their report. Clears completion
    state, the recommendation, and the saved date_complete; keeps the
    date_accepted so the screener does not have to re-accept."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    assignment = get_object_or_404(
        screening_models.ScreeningAssignment,
        pk=assignment_id,
        article=article,
    )
    assignment.reset()
    messages.add_message(
        request,
        messages.SUCCESS,
        "Screening assignment reset.",
    )
    return redirect(
        reverse("screening_article", kwargs={"article_id": article.pk}),
    )


@login_required
def screening_requests(request):
    """List screening invitations for the logged-in user on this journal.

    Pending requests are those not yet declined and not yet complete;
    completed requests are those the screener has already submitted.
    """
    base = screening_models.ScreeningAssignment.objects.filter(
        screener=request.user,
        article__journal=request.journal,
    ).select_related("article", "screening_round")
    pending = base.filter(date_declined__isnull=True, is_complete=False)
    completed = base.filter(
        Q(is_complete=True) | Q(date_declined__isnull=False),
    ).order_by("-date_complete", "-date_declined")

    template = "admin/screening/requests.html"
    context = {"pending": pending, "completed": completed}
    return render(request, template, context)


@require_POST
@screener_for_assignment_required
def accept_screening_request(request, assignment_id, assignment=None):
    """Record the screener's acceptance of an invitation."""
    if assignment.date_declined:
        messages.add_message(
            request,
            messages.WARNING,
            "This screening request has already been declined.",
        )
        return redirect(reverse("screening_requests"))

    if assignment.accept():
        messages.add_message(
            request,
            messages.SUCCESS,
            "Screening request accepted.",
        )
    return redirect(reverse("do_screening", kwargs={"assignment_id": assignment.pk}))


@require_POST
@screener_for_assignment_required
def decline_screening_request(request, assignment_id, assignment=None):
    """Record the screener's decline of an invitation."""
    if assignment.is_complete:
        messages.add_message(
            request,
            messages.WARNING,
            "This screening report is already complete and cannot be declined.",
        )
        return redirect(reverse("screening_requests"))

    if assignment.decline():
        messages.add_message(
            request,
            messages.SUCCESS,
            "Screening request declined.",
        )
    return redirect(reverse("screening_requests"))


@screener_or_editor_for_assignment_required
def do_screening(request, assignment_id, assignment=None):
    """The screener fills out the screening form and records a
    recommendation. POST submits the report, marking the assignment
    complete. Editors may access this page to submit on behalf of the
    screener."""
    if assignment.date_declined:
        raise Http404
    assignment.accept()

    form_class = (
        forms.build_screening_form_class(assignment.form) if assignment.form else None
    )
    initial_recommendation = {
        "recommendation": assignment.recommendation or "",
        "suggested_reviewers": assignment.suggested_reviewers or "",
        "comments_for_editor": assignment.comments_for_editor or "",
    }

    screening_form = form_class(request.POST or None) if form_class else None
    recommendation_form = forms.ScreeningRecommendationForm(
        request.POST or None,
        initial=initial_recommendation,
    )

    if request.method == "POST":
        screening_form_valid = screening_form.is_valid() if screening_form else True
        recommendation_valid = recommendation_form.is_valid()
        if screening_form_valid and recommendation_valid:
            if screening_form is not None:
                assignment.save_screening_form(screening_form)
            assignment.complete(
                recommendation=recommendation_form.cleaned_data["recommendation"],
                suggested_reviewers=recommendation_form.cleaned_data.get(
                    "suggested_reviewers",
                    "",
                ),
                comments_for_editor=recommendation_form.cleaned_data.get(
                    "comments_for_editor",
                    "",
                ),
            )
            event_logic.Events.raise_event(
                event_logic.Events.ON_SCREENING_COMPLETE,
                task_object=assignment.article,
                request=request,
                screening_assignment=assignment,
            )
            return redirect(
                reverse("screening_thanks", kwargs={"assignment_id": assignment.pk})
            )

    template = "admin/screening/do_screening.html"
    context = {
        "assignment": assignment,
        "article": assignment.article,
        "screening_form": screening_form,
        "recommendation_form": recommendation_form,
        "back_url": logic.back_url_for_assignment(request, assignment),
    }
    return render(request, template, context)


@screener_or_editor_for_assignment_required
def screening_thanks(request, assignment_id, assignment=None):
    """Confirmation page after a screening report is submitted."""
    template = "admin/screening/thanks.html"
    context = {
        "assignment": assignment,
        "article": assignment.article,
        "back_url": logic.back_url_for_assignment(request, assignment),
    }
    return render(request, template, context)


@editor_user_required
@require_POST
def move_to_next_stage(request, article_id):
    """Move an article out of screening into whichever workflow element
    follows it for this journal. Mirrors the editor_assignment exit
    action: the managing editor takes the article forward whenever they
    are satisfied with the screening reports — no formal decision
    artefact is recorded here.
    """
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )

    next_element = core_workflow.get_next_workflow_element(
        request.journal,
        "screening",
    )
    if next_element is None:
        messages.add_message(
            request,
            messages.WARNING,
            "There is no next workflow element configured after screening.",
        )
        return redirect(reverse("screening_article", kwargs={"article_id": article.pk}))

    # Pre-create the next stage's artefacts (e.g. ReviewRound 1) so they
    # exist when the user lands on the next page.
    logic.setup_after_screening(article, next_element)

    # Delegate the stage transition, log entry, and redirect to the
    # canonical core.workflow machinery.
    workflow = request.journal.workflow()
    current_element = workflow.elements.get(element_name="screening")
    response = core_workflow.workflow_next(
        handshake_url=current_element.handshake_url,
        request=request,
        article=article,
        switch_stage=True,
    )

    # Author notification — fired after the stage transition has been
    # logged so any per-author tasks downstream see the new stage.
    event_logic.Events.raise_event(
        event_logic.Events.ON_SCREENING_PASSED,
        task_object=article,
        request=request,
        article=article,
        next_workflow_element=next_element,
    )
    if response:
        if request.GET.get("return", None):
            return redirect(request.GET.get("return"))
        return response
    return redirect(reverse("core_dashboard"))


@editor_user_required
def request_screening_revisions(request, article_id):
    """Editor opens a revision request, asking the corresponding author
    to revise in place. Article remains in screening stage; on author
    completion a new ScreeningRound is opened automatically."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    open_revision = screening_models.ScreeningRevisionRequest.objects.open_for_article(
        article,
    )
    if open_revision:
        messages.add_message(
            request,
            messages.WARNING,
            "A revision request is already open on this article. "
            "Only one revision task may be open at a time.",
        )
        return redirect(
            reverse(
                "view_screening_revision",
                kwargs={"revision_id": open_revision.pk},
            )
        )

    form = forms.ScreeningRevisionRequestForm(
        request.POST or None,
        article=article,
        editor=request.user,
    )
    if request.method == "POST" and form.is_valid():
        revision = form.save()
        return redirect(
            reverse(
                "screening_revision_notification",
                kwargs={
                    "article_id": article.pk,
                    "revision_id": revision.pk,
                },
            )
        )

    template = "admin/screening/request_revisions.html"
    context = {"article": article, "form": form}
    return render(request, template, context)


@editor_user_required
def screening_revision_notification(request, article_id, revision_id):
    """Preview and edit the revision-request email before sending it to
    the corresponding author. POST sends the email (or skips it) and
    raises ON_SCREENING_REVISIONS_REQUESTED with the edited email body."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    revision = get_object_or_404(
        screening_models.ScreeningRevisionRequest,
        pk=revision_id,
        article=article,
    )

    do_revisions_url = request.journal.site_url(
        reverse("do_screening_revisions", kwargs={"revision_id": revision.pk}),
    )
    email_context = {
        "article": article,
        "screening_revision": revision,
        "do_revisions_url": do_revisions_url,
    }
    form = core_forms.SettingEmailForm(
        setting_name="screening_revisions_requested",
        email_context=email_context,
        request=request,
    )

    if request.method == "POST":
        form = core_forms.SettingEmailForm(
            request.POST,
            request.FILES,
            setting_name="screening_revisions_requested",
            email_context=email_context,
            request=request,
        )
        skip = request.POST.get("skip")
        if skip or form.is_valid():
            event_logic.Events.raise_event(
                event_logic.Events.ON_SCREENING_REVISIONS_REQUESTED,
                task_object=article,
                request=request,
                screening_revision=revision,
                email_data=form.as_dataclass() if not skip else None,
                skip=bool(skip),
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                (
                    "Revision request created (email skipped)."
                    if skip
                    else "Revision request sent to the corresponding author."
                ),
            )
            return redirect(
                reverse("screening_article", kwargs={"article_id": article.pk}),
            )

    template = "admin/screening/revision_notification.html"
    context = {
        "article": article,
        "revision": revision,
        "form": form,
    }
    return render(request, template, context)


@editor_user_required
@require_POST
def withdraw_screening_revisions(request, article_id, revision_id):
    """Editor cancels an open revision request. Sets date_cancelled and
    fires ON_SCREENING_REVISION_WITHDRAWN so the author is notified."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    revision = get_object_or_404(
        screening_models.ScreeningRevisionRequest,
        pk=revision_id,
        article=article,
        date_completed__isnull=True,
        date_cancelled__isnull=True,
    )
    revision.cancel()
    event_logic.Events.raise_event(
        event_logic.Events.ON_SCREENING_REVISION_WITHDRAWN,
        task_object=article,
        request=request,
        screening_revision=revision,
    )
    messages.add_message(
        request,
        messages.SUCCESS,
        "Revision request withdrawn.",
    )
    return redirect(
        reverse("screening_article", kwargs={"article_id": article.pk}),
    )


@editor_user_required
def edit_screening_revisions(request, article_id, revision_id):
    """Editor amends an open revision request (due date, type, note)
    before the author submits."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    revision = get_object_or_404(
        screening_models.ScreeningRevisionRequest,
        pk=revision_id,
        article=article,
        date_completed__isnull=True,
        date_cancelled__isnull=True,
    )
    form = forms.ScreeningRevisionRequestForm(
        request.POST or None,
        instance=revision,
        article=article,
        editor=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Revision request updated.",
        )
        return redirect(
            reverse(
                "view_screening_revision",
                kwargs={"revision_id": revision.pk},
            )
        )

    template = "admin/screening/edit_revisions.html"
    context = {"article": article, "revision": revision, "form": form}
    return render(request, template, context)


@login_required
def do_screening_revisions(request, revision_id):
    """Author surface for completing a screening revision. The author
    uses Janeway's existing article-files mechanism to upload the
    revised manuscript and may add a covering letter. Submitting marks
    the revision complete and opens a new ScreeningRound."""
    revision = get_object_or_404(
        screening_models.ScreeningRevisionRequest,
        pk=revision_id,
        article__journal=request.journal,
    )
    if request.user != revision.article.correspondence_author:
        raise Http404
    if revision.date_completed or revision.date_cancelled:
        return redirect(
            reverse(
                "view_screening_revision",
                kwargs={"revision_id": revision.pk},
            )
        )

    form = forms.AuthorRevisionResponseForm(request.POST or None, instance=revision)
    if request.method == "POST":
        if "save" in request.POST and form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Covering letter saved. Come back any time to finish.",
            )
            return redirect(
                reverse(
                    "do_screening_revisions",
                    kwargs={"revision_id": revision.pk},
                )
            )
        if "submit" in request.POST and form.is_valid():
            form.save()
            revision.complete()
            event_logic.Events.raise_event(
                event_logic.Events.ON_SCREENING_REVISIONS_COMPLETED,
                task_object=revision.article,
                request=request,
                screening_revision=revision,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                "Revisions submitted. The editorial team will be in touch.",
            )
            return redirect(reverse("core_dashboard"))

    template = "admin/screening/do_revisions.html"
    context = {
        "article": revision.article,
        "revision": revision,
        "form": form,
    }
    return render(request, template, context)


@login_required
def screening_revisions_replace_file(request, revision_id, file_id):
    """Replace one of the article's files with a new upload, as part of
    the author's revision response. Mirrors review's `replace_file`."""
    from core import files as core_files
    from core import models as core_models

    revision = logic.get_open_revision_for_author(request, revision_id)
    file = get_object_or_404(core_models.File, pk=file_id)

    if request.method == "POST" and request.FILES:
        uploaded_file = request.FILES.get("replacement-file")
        if uploaded_file:
            label = request.POST.get("label") or file.label
            new_file = core_files.save_file_to_article(
                uploaded_file,
                revision.article,
                request.user,
                replace=file,
                is_galley=False,
                label=label,
            )
            core_files.replace_file(
                revision.article,
                file,
                new_file,
                retain_old_label=False,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                "File replaced.",
            )
        return redirect(
            reverse("do_screening_revisions", kwargs={"revision_id": revision.pk}),
        )

    template = "admin/screening/replace_file.html"
    context = {"revision": revision, "article": revision.article, "file": file}
    return render(request, template, context)


@login_required
def screening_revisions_upload_new_file(request, revision_id):
    """Upload a new file (manuscript or data/figure) to the article as
    part of the author's revision response. Mirrors review's
    `upload_new_file`."""
    from core import files as core_files

    revision = logic.get_open_revision_for_author(request, revision_id)
    article = revision.article

    if request.method == "POST" and request.FILES:
        file_type = request.POST.get("file_type")
        uploaded_file = request.FILES.get("file")
        label = request.POST.get("label") or "Author Upload"
        if uploaded_file:
            new_file = core_files.save_file_to_article(
                uploaded_file,
                article,
                request.user,
                label=label,
            )
            if file_type == "manuscript":
                article.manuscript_files.add(new_file)
            else:
                article.data_figure_files.add(new_file)
            messages.add_message(
                request,
                messages.SUCCESS,
                "File uploaded.",
            )
        return redirect(
            reverse("do_screening_revisions", kwargs={"revision_id": revision.pk}),
        )

    template = "admin/screening/upload_new_file.html"
    context = {"revision": revision, "article": article}
    return render(request, template, context)


@editor_user_required
def view_screening_revision(request, revision_id):
    """Editor read-only view of a completed (or pending) revision."""
    if not journal_has_screening_element(request.journal):
        raise Http404("Screening is not enabled for this journal.")

    revision = get_object_or_404(
        screening_models.ScreeningRevisionRequest,
        pk=revision_id,
        article__journal=request.journal,
    )
    template = "admin/screening/view_revision.html"
    context = {"article": revision.article, "revision": revision}
    return render(request, template, context)


@senior_editor_user_required
def screening_checklist_templates(request):
    """List technical-check checklist templates for this journal, with
    create + delete actions."""
    template_list = screening_models.TechnicalChecklistTemplate.objects.filter(
        journal=request.journal,
        deleted=False,
    )
    form = forms.ChecklistTemplateForm()

    if request.method == "POST":
        if "delete" in request.POST:
            obj = get_object_or_404(
                screening_models.TechnicalChecklistTemplate,
                pk=request.POST["delete"],
                journal=request.journal,
            )
            obj.deleted = True
            obj.save()
            messages.add_message(request, messages.SUCCESS, "Template deleted.")
            return redirect(reverse("screening_checklist_templates"))

        form = forms.ChecklistTemplateForm(request.POST)
        if form.is_valid():
            new_template = form.save(commit=False)
            new_template.journal = request.journal
            new_template.save()
            return redirect(
                reverse(
                    "edit_screening_checklist_template",
                    kwargs={"template_id": new_template.pk},
                )
            )

    template = "admin/screening/manager/checklist_templates.html"
    context = {"template_list": template_list, "form": form}
    return render(request, template, context)


@senior_editor_user_required
def edit_screening_checklist_template(request, template_id, item_id=None):
    """Edit a checklist template's metadata and its items."""
    edit_template = get_object_or_404(
        screening_models.TechnicalChecklistTemplate,
        pk=template_id,
        journal=request.journal,
    )
    form = forms.ChecklistTemplateForm(instance=edit_template)
    item_form = forms.ChecklistTemplateItemForm()
    item, modal = None, None

    if item_id:
        item = get_object_or_404(
            screening_models.TechnicalChecklistTemplateItem,
            pk=item_id,
            template=edit_template,
        )
        item_form = forms.ChecklistTemplateItemForm(instance=item)
        modal = "item"

    if request.method == "POST":
        if "delete" in request.POST:
            target = get_object_or_404(
                screening_models.TechnicalChecklistTemplateItem,
                pk=request.POST["delete"],
                template=edit_template,
            )
            target.delete()
            return redirect(
                reverse(
                    "edit_screening_checklist_template",
                    kwargs={"template_id": edit_template.pk},
                )
            )

        if "item" in request.POST:
            if item_id:
                item_form = forms.ChecklistTemplateItemForm(
                    request.POST,
                    instance=item,
                )
            else:
                item_form = forms.ChecklistTemplateItemForm(request.POST)
            if item_form.is_valid():
                saved = item_form.save(commit=False)
                saved.template = edit_template
                saved.save()
                return redirect(
                    reverse(
                        "edit_screening_checklist_template",
                        kwargs={"template_id": edit_template.pk},
                    )
                )

        if "template" in request.POST:
            form = forms.ChecklistTemplateForm(
                request.POST,
                instance=edit_template,
            )
            if form.is_valid():
                form.save()
                return redirect(
                    reverse(
                        "edit_screening_checklist_template",
                        kwargs={"template_id": edit_template.pk},
                    )
                )

    template = "admin/screening/manager/edit_checklist_template.html"
    context = {
        "edit_template": edit_template,
        "form": form,
        "item_form": item_form,
        "modal": modal,
    }
    return render(request, template, context)


@editor_user_required
def toggle_checklist_item(request, item_id):
    """Toggle a single checklist item's complete state for an article in
    Screening. POST-only; records who toggled it and when."""
    if request.method != "POST":
        return redirect(reverse("screening_list"))

    item = get_object_or_404(
        screening_models.TechnicalChecklistItem,
        pk=item_id,
        checklist__article__journal=request.journal,
    )
    item.is_complete = not item.is_complete
    if item.is_complete:
        item.completed_by = request.user
        item.completed_at = timezone.now()
    else:
        item.completed_by = None
        item.completed_at = None
    item.save()
    return logic.render_checklist_item_response(request, item)


@editor_user_required
def switch_checklist_template(request, article_id):
    """Replace the checklist applied to an article with a different
    journal-level template. Existing item state is discarded — the
    operation re-seeds items from the chosen template."""
    if request.method != "POST":
        return redirect(reverse("screening_list"))

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
        stage=submission_models.STAGE_SCREENING,
    )
    template = get_object_or_404(
        screening_models.TechnicalChecklistTemplate,
        pk=request.POST.get("template_id"),
        journal=request.journal,
        deleted=False,
    )
    checklist, _ = screening_models.TechnicalChecklist.objects.get_or_create(
        article=article,
    )
    checklist.template = template
    checklist.save()
    checklist.items.all().delete()
    for tpl_item in template.items.all():
        screening_models.TechnicalChecklistItem.objects.create(
            checklist=checklist,
            template_item=tpl_item,
            label=tpl_item.label,
            order=tpl_item.order,
        )

    checklist_templates = screening_models.TechnicalChecklistTemplate.objects.filter(
        journal=request.journal,
        deleted=False,
    )
    if request.headers.get("HX-Request"):
        return render(
            request,
            "admin/screening/_checklist_panel.html",
            {
                "article": article,
                "checklist": checklist,
                "checklist_templates": checklist_templates,
            },
        )
    return redirect(
        reverse("screening_article", kwargs={"article_id": article.pk}),
    )


@editor_user_required
def save_checklist_item_comment(request, item_id):
    """Persist the editor's comment on a checklist item."""
    if request.method != "POST":
        return redirect(reverse("screening_list"))

    item = get_object_or_404(
        screening_models.TechnicalChecklistItem,
        pk=item_id,
        checklist__article__journal=request.journal,
    )
    item.comment = request.POST.get("comment", "")[:5000]
    item.save()
    return logic.render_checklist_item_response(request, item)


@senior_editor_user_required
def screening_pool(request):
    """Per-journal manager page selecting which editorial groups
    contribute members to the screener pool."""
    pool, _ = screening_models.ScreeningPool.objects.get_or_create(
        journal=request.journal,
    )
    form = forms.ScreeningPoolForm(
        request.POST or None,
        instance=pool,
        journal=request.journal,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Screener pool updated.",
        )
        return redirect(reverse("screening_pool"))

    template = "admin/screening/manager/screening_pool.html"
    context = {"form": form, "pool": pool}
    return render(request, template, context)


@senior_editor_user_required
def screening_forms(request):
    """List screening forms on this journal and offer creation of new
    forms or soft-deletion of existing ones."""
    form_list = screening_models.ScreeningForm.objects.filter(
        journal=request.journal,
        deleted=False,
    )

    form = forms.NewScreeningForm()

    if request.method == "POST":
        if "delete" in request.POST:
            form_id = request.POST["delete"]
            form_obj = get_object_or_404(
                screening_models.ScreeningForm,
                id=form_id,
                journal=request.journal,
            )
            form_obj.deleted = True
            form_obj.save()
            messages.add_message(request, messages.SUCCESS, "Screening form deleted.")
            return redirect(reverse("screening_forms"))

        form = forms.NewScreeningForm(request.POST)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.journal = request.journal
            new_form.save()
            messages.add_message(request, messages.SUCCESS, "Screening form created.")
            return redirect(
                reverse("edit_screening_form", kwargs={"form_id": new_form.pk})
            )

    template = "admin/screening/manager/screening_forms.html"
    context = {"form_list": form_list, "form": form}
    return render(request, template, context)


@senior_editor_user_required
def edit_screening_form(request, form_id, element_id=None):
    """Edit a screening form's metadata and manage its elements."""
    edit_form = get_object_or_404(
        screening_models.ScreeningForm,
        pk=form_id,
        journal=request.journal,
    )
    form = forms.NewScreeningForm(instance=edit_form)
    element_form = forms.ScreeningElementForm()
    element, modal = None, None

    if element_id:
        element = get_object_or_404(
            screening_models.ScreeningFormElement,
            pk=element_id,
            screeningform=edit_form,
        )
        modal = "element"
        element_form = forms.ScreeningElementForm(instance=element)

    if request.method == "POST":
        if "delete" in request.POST:
            delete_id = request.POST.get("delete")
            element_to_delete = get_object_or_404(
                screening_models.ScreeningFormElement,
                pk=delete_id,
                screeningform=edit_form,
            )
            element_to_delete.delete()
            messages.add_message(request, messages.SUCCESS, "Element deleted.")
            return redirect(
                reverse("edit_screening_form", kwargs={"form_id": edit_form.pk})
            )

        if "element" in request.POST:
            if element_id:
                element_form = forms.ScreeningElementForm(
                    request.POST,
                    instance=element,
                )
            else:
                element_form = forms.ScreeningElementForm(request.POST)
            if element_form.is_valid():
                saved_element = element_form.save()
                edit_form.elements.add(saved_element)
                messages.add_message(request, messages.SUCCESS, "Element saved.")
                return redirect(
                    reverse(
                        "edit_screening_form",
                        kwargs={"form_id": edit_form.pk},
                    )
                )

        if "screening_form" in request.POST:
            form = forms.NewScreeningForm(request.POST, instance=edit_form)
            if form.is_valid():
                form.save()
                messages.add_message(request, messages.SUCCESS, "Form updated.")
                return redirect(
                    reverse(
                        "edit_screening_form",
                        kwargs={"form_id": edit_form.pk},
                    )
                )

    template = "admin/screening/manager/edit_screening_form.html"
    context = {
        "form": form,
        "edit_form": edit_form,
        "element_form": element_form,
        "modal": modal,
    }
    return render(request, template, context)

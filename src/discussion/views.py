from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest

from core.views import BaseUserList
from core import models as core_models
from discussion import forms, models
from repository import models as repository_models
from security.decorators import can_access_thread, editor_user_required
from submission import models as submission_models
from review.models import ReviewAssignment
from copyediting.models import CopyeditAssignment
from typesetting.models import TypesettingAssignment


def threads(request, object_type, object_id, thread_id=None):
    if object_type == "article":
        obj = get_object_or_404(
            submission_models.Article,
            pk=object_id,
            journal=request.journal,
        )
    else:
        obj = get_object_or_404(
            repository_models.Preprint,
            pk=object_id,
            repository=request.repository,
        )

    return render(
        request,
        "admin/discussion/threads_base.html",
        {
            "object": obj,
            "object_type": object_type,
            "active_thread_id": thread_id,
        },
    )


@require_POST
@can_access_thread
def add_post(request, thread_id):
    thread = get_object_or_404(models.Thread, pk=thread_id)

    body = request.POST.get("new_post", "").strip()
    if body:
        thread.create_post(request.user, body)

    return render(
        request,
        "admin/discussion/partials/thread_detail.html",
        {
            "thread": thread,
            "posts": thread.posts(),
            "object_type": thread.object_string(),
            "object": thread.article or thread.preprint,
        },
    )


def create_thread(request, object_type, object_id):
    if object_type == "article":
        obj = get_object_or_404(
            submission_models.Article,
            pk=object_id,
            journal=request.journal,
        )
    else:
        obj = get_object_or_404(
            repository_models.Preprint,
            pk=object_id,
            repository=request.repository,
        )

    if request.method == "POST":
        form = forms.ThreadForm(
            request.POST,
            object=obj,
            object_type=object_type,
            owner=request.user,
        )
        if form.is_valid():
            thread = form.save(commit=False)
            # 🔸 attach the object here!
            if object_type == "article":
                thread.article = obj
            else:
                thread.preprint = obj
            thread.owner = request.user
            thread.save()

            # ✅ return updated list partial
            threads = models.Thread.objects.filter(
                article=obj if object_type == "article" else None,
                preprint=obj if object_type == "preprint" else None,
            )
            html = render_to_string(
                "admin/discussion/partials/thread_list.html",
                {
                    "object": obj,
                    "object_type": object_type,
                    "threads": threads,
                },
                request=request,
            )
            return HttpResponse(html)
    else:
        form = forms.ThreadForm(
            object=obj,
            object_type=object_type,
            owner=request.user,
        )

    return render(
        request,
        "admin/discussion/partials/new_thread_form.html",
        {
            "form": form,
            "object": obj,
            "object_type": object_type,
        },
    )


@method_decorator(editor_user_required, name="dispatch")
class ThreadInviteUserListView(BaseUserList):
    """
    Reuses the BaseUserList to display potential invitees for a discussion thread.
    Only lists active users and excludes participants already in the thread.
    """
    template_name = "admin/discussion/partials/invite_search.html"

    def dispatch(self, request, *args, **kwargs):
        self.thread = get_object_or_404(
            models.Thread,
            pk=self.kwargs.get("thread_id"),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(is_active=True)

        if self.request.journal:
            qs = qs.filter(accountrole__journal=self.request.journal)

        participant_ids = self.thread.participants.values_list("id", flat=True)
        qs = qs.exclude(pk__in=participant_ids)

        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["thread"] = self.thread

        article = self.thread.article

        # Collect IDs of users in various roles
        reviewers = ReviewAssignment.objects.filter(
            article=article
        ).values_list("reviewer", flat=True)

        copyeditors = CopyeditAssignment.objects.filter(
            article=article
        ).values_list("copyeditor", flat=True)

        typesetters = TypesettingAssignment.objects.filter(
            round__article=article
        ).values_list("typesetter", flat=True)

        managers = TypesettingAssignment.objects.filter(
            round__article=article
        ).values_list("manager", flat=True)

        authors = article.authors.values_list("pk", flat=True)

        role_ids = set(
            filter(
                None,
                list(reviewers)
                + list(copyeditors)
                + list(typesetters)
                + list(managers)
                + list(authors),
            )
        )

        # Exclude participants and filter only active users here too
        role_ids = role_ids.difference(set(self.thread.participants.values_list("pk", flat=True)))

        ctx["role_users"] = self.model.objects.filter(
            pk__in=role_ids,
            is_active=True
        ).distinct()

        return ctx


@require_POST
@editor_user_required
def add_participant(request, thread_id):
    thread = get_object_or_404(models.Thread, pk=thread_id)
    user_id = request.POST.get("user_id")
    if not user_id:
        return HttpResponseBadRequest("Missing user_id")
    user = get_object_or_404(core_models.Account, pk=user_id)
    user = get_object_or_404(core_models.Account, pk=user_id)
    thread.participants.add(user)
    return HttpResponse(status=204)

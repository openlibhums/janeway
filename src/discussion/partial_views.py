from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from discussion import forms, models
from repository import models as repository_models
from security.decorators import can_access_thread, editor_user_required
from submission import models as submission_models
from core import models as core_models


from core.views import BaseUserList
from review.models import ReviewAssignment
from copyediting.models import CopyeditAssignment
from typesetting.models import TypesettingAssignment


@login_required
def threads_list_partial(
    request,
    object_type,
    object_id,
):
    """
    Returns only the list of threads the current user can access.
    """
    if object_type == "article":
        object_to_get = get_object_or_404(
            submission_models.Article,
            pk=object_id,
            journal=request.journal,
        )
        qs = models.Thread.objects.filter(article=object_to_get)
    else:
        object_to_get = get_object_or_404(
            repository_models.Preprint,
            pk=object_id,
            repository=request.repository,
        )
        qs = models.Thread.objects.filter(preprint=object_to_get)

    # Filter threads by access
    accessible_threads = [
        t
        for t in qs.select_related("owner").prefetch_related("participants")
        if t.user_can_access(request.user)
    ]

    return render(
        request,
        "admin/discussion/partials/thread_list.html",
        {
            "threads": accessible_threads,
            "object": object_to_get,
            "object_type": object_type,
        },
    )


@can_access_thread
def thread_detail_partial(
    request,
    object_type,
    object_id,
    thread_id,
):
    """
    Returns a single thread detail.
    """
    thread = get_object_or_404(
        models.Thread,
        pk=thread_id,
    )

    posts = thread.posts()
    return render(
        request,
        "admin/discussion/partials/thread_detail.html",
        {
            "thread": thread,
            "posts": posts,
            "object_type": object_type,
            "object_id": object_id,
        },
    )


@editor_user_required
def new_thread_form_partial(
    request,
    object_type,
    object_id,
):
    """
    Renders a new thread creation form as a partial.
    """
    if object_type == "article":
        object_to_get = get_object_or_404(
            submission_models.Article,
            pk=object_id,
            journal=request.journal,
        )
    else:
        object_to_get = get_object_or_404(
            repository_models.Preprint,
            pk=object_id,
            repository=request.repository,
        )

    from discussion import forms

    form = forms.ThreadForm(
        object=object_to_get,
        object_type=object_type,
        owner=request.user,
    )

    return render(
        request,
        "admin/discussion/partials/new_thread_form.html",
        {
            "form": form,
            "object": object_to_get,
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

        # Build a mapping of user_id -> list of roles
        role_mapping = {}

        for user_id in ReviewAssignment.objects.filter(article=article).values_list(
            "reviewer", flat=True
        ):
            if user_id:
                role_mapping.setdefault(user_id, []).append("Reviewer")

        for user_id in CopyeditAssignment.objects.filter(article=article).values_list(
            "copyeditor", flat=True
        ):
            if user_id:
                role_mapping.setdefault(user_id, []).append("Copyeditor")

        for user_id in TypesettingAssignment.objects.filter(
            round__article=article
        ).values_list("typesetter", flat=True):
            if user_id:
                role_mapping.setdefault(user_id, []).append("Typesetter")
        for user_id in TypesettingAssignment.objects.filter(
            round__article=article
        ).values_list("manager", flat=True):
            if user_id:
                role_mapping.setdefault(user_id, []).append("Production Manager")

        for user_id in article.authors.values_list("pk", flat=True):
            if user_id:
                role_mapping.setdefault(user_id, []).append("Author")

        # Exclude participants
        participant_ids = set(self.thread.participants.values_list("pk", flat=True))
        role_ids = set(role_mapping.keys()).difference(participant_ids)

        # Get users and attach their roles
        role_users = self.model.objects.filter(
            pk__in=role_ids, is_active=True
        ).distinct()

        for user in role_users:
            user.article_roles = role_mapping.get(user.pk, [])

        ctx["role_users"] = role_users

        return ctx


@require_POST
@editor_user_required
def add_participant(request, thread_id):
    thread = get_object_or_404(models.Thread, pk=thread_id)
    user_id = request.POST.get("user_id")
    if not user_id:
        return HttpResponseBadRequest("Missing user_id")
    user = get_object_or_404(core_models.Account, pk=user_id)
    thread.participants.add(user)
    return HttpResponse(status=204)


@editor_user_required
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
            if object_type == "article":
                thread.article = obj
            else:
                thread.preprint = obj
            thread.owner = request.user
            thread.save()

            # return updated list partial
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

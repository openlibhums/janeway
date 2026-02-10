import os
from uuid import uuid4

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from core import files as core_files
from core import models as core_models
from core.views import BaseUserList
from discussion import forms, models
from events import logic as event_logic
from repository import models as repository_models
from security.decorators import can_access_thread, editor_user_required
from submission import models as submission_models
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

    for t in accessible_threads:
        t.unread_count = t.unread_count_for(request.user)

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

    # Mark all posts as read for this user
    for post in posts:
        post.read_by.add(request.user)

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

        if article:
            for user_id in ReviewAssignment.objects.filter(article=article).values_list(
                "reviewer", flat=True
            ):
                if user_id:
                    role_mapping.setdefault(user_id, []).append("Reviewer")

            for user_id in CopyeditAssignment.objects.filter(
                article=article
            ).values_list("copyeditor", flat=True):
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
    event_logic.Events.raise_event(
        event_logic.Events.ON_DISCUSSION_PARTICIPANT_ADDED,
        thread=thread,
        participant=user,
        added_by=request.user,
        request=request,
    )
    thread.create_system_post(
        actor=request.user,
        body=f"{request.user.full_name()} added {user.full_name()} to the discussion",
    )
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

            # return updated list partial, filtered by access
            if object_type == "article":
                qs = models.Thread.objects.filter(article=obj)
            else:
                qs = models.Thread.objects.filter(preprint=obj)
            accessible_threads = [
                t
                for t in qs.select_related("owner").prefetch_related("participants")
                if t.user_can_access(request.user)
            ]
            for t in accessible_threads:
                t.unread_count = t.unread_count_for(request.user)
            html = render_to_string(
                "admin/discussion/partials/thread_list.html",
                {
                    "object": obj,
                    "object_type": object_type,
                    "threads": accessible_threads,
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
    uploaded_file = request.FILES.get("file")

    if body or uploaded_file:
        post = thread.create_post(request.user, body or "")

        if uploaded_file:
            file_obj = save_file_to_discussion(uploaded_file, thread, request.user)
            post.file = file_obj
            post.save(update_fields=["file"])

        event_logic.Events.raise_event(
            event_logic.Events.ON_DISCUSSION_POST_CREATED,
            thread=thread,
            post=post,
            request=request,
        )

    posts = thread.posts()

    # Mark all posts as read for this user
    for post in posts:
        post.read_by.add(request.user)

    return render(
        request,
        "admin/discussion/partials/thread_detail.html",
        {
            "thread": thread,
            "posts": posts,
            "object_type": thread.object_string(),
            "object": thread.article or thread.preprint,
        },
    )


@require_POST
@editor_user_required
def remove_participant(request, thread_id):
    thread = get_object_or_404(models.Thread, pk=thread_id)
    user_id = request.POST.get("user_id")
    if not user_id:
        return HttpResponseBadRequest("Missing user_id")
    user = get_object_or_404(core_models.Account, pk=user_id)

    # Cannot remove the thread owner
    if user == thread.owner:
        return HttpResponseBadRequest("Cannot remove the thread owner")

    thread.participants.remove(user)
    event_logic.Events.raise_event(
        event_logic.Events.ON_DISCUSSION_PARTICIPANT_REMOVED,
        thread=thread,
        participant=user,
        removed_by=request.user,
        request=request,
    )
    thread.create_system_post(
        actor=request.user,
        body=f"{request.user.full_name()} removed {user.full_name()} from the discussion",
    )
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


@require_POST
@can_access_thread
def edit_subject(request, thread_id):
    thread = get_object_or_404(models.Thread, pk=thread_id)
    new_subject = request.POST.get("subject", "").strip()

    if not new_subject or len(new_subject) > 300:
        return HttpResponseBadRequest("Subject must be between 1 and 300 characters.")

    old_subject = thread.subject
    if new_subject != old_subject:
        thread.subject = new_subject
        thread.save(update_fields=["subject"])
        thread.create_system_post(
            actor=request.user,
            body=f'{request.user.full_name()} changed the title from "{old_subject}" to "{new_subject}"',
        )

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


def save_file_to_discussion(uploaded_file, thread, owner):
    """Save an uploaded file into the discussion folder and return a core.File."""
    original_filename = str(uploaded_file.name)
    filename = str(uuid4()) + str(os.path.splitext(original_filename)[1])
    folder_structure = os.path.join(
        settings.BASE_DIR,
        "files",
        "discussions",
        str(thread.pk),
    )
    core_files.save_file_to_disk(uploaded_file, filename, folder_structure)
    file_mime = core_files.file_path_mime(os.path.join(folder_structure, filename))

    new_file = core_models.File(
        mime_type=file_mime,
        original_filename=original_filename,
        uuid_filename=filename,
        owner=owner,
        label="Discussion attachment",
    )
    new_file.save()
    return new_file


@require_POST
@can_access_thread
def edit_post(request, thread_id, post_id):
    thread = get_object_or_404(models.Thread, pk=thread_id)
    post = get_object_or_404(models.Post, pk=post_id, thread=thread)

    # Only the post owner can edit
    if post.owner != request.user:
        return HttpResponseBadRequest("You can only edit your own posts.")

    # System messages cannot be edited
    if post.is_system_message:
        return HttpResponseBadRequest("System messages cannot be edited.")

    body = request.POST.get("body", "").strip()
    if not body:
        return HttpResponseBadRequest("Post body cannot be empty.")

    post.body = body
    post.edited = timezone.now()
    post.save(update_fields=["body", "edited"])

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


@can_access_thread
def serve_discussion_file(request, thread_id, file_id):
    thread = get_object_or_404(models.Thread, pk=thread_id)
    file_obj = get_object_or_404(core_models.File, pk=file_id)

    # Verify this file actually belongs to a post in this thread
    if not thread.posts_related.filter(file=file_obj).exists():
        return HttpResponseBadRequest("File not found in this thread.")

    return core_files.serve_any_file(
        request,
        file_obj,
        path_parts=("discussions", str(thread.pk)),
    )

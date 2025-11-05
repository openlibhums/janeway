from django.shortcuts import render, get_object_or_404
from discussion.models import Thread
from submission import models as submission_models
from repository import models as repository_models
from security.decorators import can_access_thread


def threads_list_partial(
    request,
    object_type,
    object_id,
):
    """
    Returns only the list of threads the current user can access.
    No decorator needed here since we filter per-thread access.
    """
    if object_type == "article":
        object_to_get = get_object_or_404(
            submission_models.Article,
            pk=object_id,
            journal=request.journal,
        )
        qs = Thread.objects.filter(article=object_to_get)
    else:
        object_to_get = get_object_or_404(
            repository_models.Preprint,
            pk=object_id,
            repository=request.repository,
        )
        qs = Thread.objects.filter(preprint=object_to_get)

    # Filter threads by access
    accessible_threads = [
        t for t in qs.select_related("owner").prefetch_related("participants")
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
    Access control happens via @can_access_thread.
    """
    thread = get_object_or_404(
        Thread,
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


def new_thread_form_partial(
    request,
    object_type,
    object_id,
):
    """
    Renders a new thread creation form as a partial.
    Useful for HTMX modals.
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

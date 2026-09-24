from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    render,
)

from discussion import logic
from repository import models as repository_models
from security.decorators import deny_access
from submission import models as submission_models


@login_required
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

    if not logic.user_can_access_object_threads(
        request.user,
        obj,
        object_type,
        journal=request.journal,
        repository=request.repository,
    ):
        deny_access(request)

    return render(
        request,
        "admin/discussion/threads_base.html",
        {
            "object": obj,
            "object_type": object_type,
            "active_thread_id": thread_id,
        },
    )

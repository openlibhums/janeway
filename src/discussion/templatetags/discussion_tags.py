from django import template
from django.urls import reverse

from discussion import logic

register = template.Library()


@register.simple_tag
def discussion_file_url(thread_pk, file_pk):
    return reverse(
        "discussion_serve_file",
        kwargs={"thread_id": thread_pk, "file_id": file_pk},
    )


@register.simple_tag
def can_manage_discussion(request):
    """
    Mirrors security.decorators.editor_or_manager so templates gate
    participant management consistently in both journal and repository
    contexts.
    """
    return logic.user_can_manage_discussions(
        request.user,
        journal=request.journal,
        repository=request.repository,
    )

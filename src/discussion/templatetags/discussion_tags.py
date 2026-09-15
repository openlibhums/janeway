from django import template
from django.urls import reverse

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
    user = request.user
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    if request.journal and user in request.journal.editors():
        return True
    if request.repository and user in request.repository.managers.all():
        return True
    return False

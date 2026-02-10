from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def discussion_file_url(thread_pk, file_pk):
    return reverse(
        "discussion_serve_file",
        kwargs={"thread_id": thread_pk, "file_id": file_pk},
    )

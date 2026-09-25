from django.core.cache import cache
from django.shortcuts import get_object_or_404, render
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)
from django.core.exceptions import ValidationError

from core import forms, models, logic
from journal import models as journal_models
from security.decorators import editor_or_journal_manager_required, role_can_access
from utils.htmx import hx_show_message


JOURNAL_IMAGE_FIELDS = {
    "header_image",
    "default_cover_image",
    "default_large_image",
    "favicon",
    "press_image_override",
    "default_profile_image",
    "default_thumbnail",
}


@require_GET
@editor_or_journal_manager_required
def alt_text_form(request):
    try:
        content_type, object_id, file_path, obj = logic.resolve_alt_text_target(
            request,
        )
    except ValidationError:
        return HttpResponseBadRequest("Invalid model or pk")

    instance = models.AltText.objects.filter(
        content_type=content_type,
        object_id=object_id,
        file_path=file_path,
    ).first()

    form = forms.AltTextForm(
        instance=instance,
        content_type=content_type,
        object_id=object_id,
        file_path=file_path,
    )

    return render(
        request,
        "core/partials/alt_text/form.html",
        {
            "form": form,
            "object": obj,
            "file_path": file_path,
            "token": file_path,
        },
    )


@require_POST
@editor_or_journal_manager_required
def alt_text_submit(request):
    try:
        content_type, object_id, file_path, obj = logic.resolve_alt_text_target(request)
    except ValidationError:
        return HttpResponseBadRequest("Invalid model or pk")

    instance = models.AltText.objects.filter(
        content_type=content_type,
        object_id=object_id,
        file_path=file_path,
    ).first()

    form = forms.AltTextForm(
        request.POST,
        instance=instance,
        content_type=content_type,
        object_id=object_id,
        file_path=file_path,
    )

    if form.is_valid():
        form.save()
        response = render(
            request,
            "core/partials/alt_text/edit_alt_text_button.html",
            {
                "object": obj,
                "token": file_path,
            },
        )
        hx_show_message(response, "Alt text saved.")
        return response

    return render(
        request,
        "core/partials/alt_text/form.html",
        {
            "form": form,
            "object": obj,
            "file_path": file_path,
        },
    )


@require_POST
@editor_or_journal_manager_required
def journal_image_upload(request, field_name):
    if field_name not in JOURNAL_IMAGE_FIELDS:
        return HttpResponseBadRequest("Invalid field name")

    if field_name == "default_thumbnail":
        logic.handle_default_thumbnail(request, request.journal, attr_form=None)
        cache.clear()
        request.journal.refresh_from_db()
    else:
        form = forms.JournalSingleImageForm(
            request.POST,
            request.FILES,
            instance=request.journal,
            field_name=field_name,
        )
        if not form.is_valid():
            return render(
                request,
                "admin/core/partials/journal_image/upload_field.html",
                {
                    "field_name": field_name,
                    "field": form[field_name],
                    "journal": request.journal,
                },
            )
        form.save()
        cache.clear()
        request.journal.refresh_from_db()

    response = _render_upload_field(request, field_name)
    return hx_show_message(response, "Image saved.")


def _render_upload_field(request, field_name):
    if field_name == "default_thumbnail":
        thumbnail_form = forms.JournalImageForm(instance=request.journal)
        field = thumbnail_form["default_thumbnail"]
    else:
        field = forms.JournalSingleImageForm(
            instance=request.journal,
            field_name=field_name,
        )[field_name]
    return render(
        request,
        "admin/core/partials/journal_image/upload_field.html",
        {
            "field_name": field_name,
            "field": field,
            "journal": request.journal,
        },
    )


@require_POST
@editor_or_journal_manager_required
def journal_image_remove(request, field_name):
    if field_name not in JOURNAL_IMAGE_FIELDS:
        return HttpResponseBadRequest("Invalid field name")

    if field_name == "default_thumbnail":
        if request.journal.thumbnail_image:
            request.journal.thumbnail_image.unlink_file(journal=request.journal)
            request.journal.thumbnail_image = None
            request.journal.save()
    else:
        setattr(request.journal, field_name, None)
        request.journal.save()

    cache.clear()
    request.journal.refresh_from_db()

    response = _render_upload_field(request, field_name)
    return hx_show_message(response, "Image removed.")


@require_GET
@role_can_access("topics")
def topic_item(request, topic_id):
    """
    Renders a single topic as a table row.
    :param request: HttpRequest object
    :param topic_id: Topic object PK
    :return: HttpResponse
    """
    topic = get_object_or_404(
        journal_models.Topic,
        id=topic_id,
        journal=request.journal,
    )

    template = "admin/core/partials/topics/topic_row.html"
    context = {
        "topic": topic,
    }
    return render(request, template, context)


@require_POST
@role_can_access("topics")
def topic_articles_update(request, topic_id):
    """
    Moves a selection of a topic's articles to another topic or removes them
    from the topic, then renders the topic's articles table.
    :param request: HttpRequest object
    :param topic_id: Topic object PK
    :return: HttpResponse
    """
    topic = get_object_or_404(
        journal_models.Topic,
        id=topic_id,
        journal=request.journal,
    )
    other_topics = journal_models.Topic.objects.filter(
        journal=request.journal,
    ).exclude(pk=topic.pk)

    articles = topic.article_set.filter(
        journal=request.journal,
        pk__in=[pk for pk in request.POST.getlist("articles") if pk.isdigit()],
    )
    action = request.POST.get("action")
    new_topic = None
    topic_pk = request.POST.get("topic", "")
    if action == "move" and topic_pk.isdigit():
        new_topic = other_topics.filter(pk=topic_pk).first()

    if not articles:
        message, level = _("No articles were selected."), "warning"
    elif action == "move" and not new_topic:
        message, level = _("Select the topic to move the articles to."), "warning"
    elif action not in ("move", "clear"):
        message, level = _("Unknown action."), "error"
    else:
        count = len(articles)
        for article in articles:
            article.topic = new_topic
            article.save()
        if new_topic:
            message = _("%(count)s article(s) moved to %(topic)s.") % {
                "count": count,
                "topic": new_topic.title,
            }
        else:
            message = _("%(count)s article(s) removed from %(topic)s.") % {
                "count": count,
                "topic": topic.title,
            }
        level = "success"

    response = render(
        request,
        "admin/core/partials/topics/topic_articles_table.html",
        {"topic": topic},
    )
    return hx_show_message(response, message, level=level)


@require_http_methods(["GET", "POST", "DELETE"])
@role_can_access("topics")
def topic_form(request, topic_id=None):
    """
    Renders, saves or deletes a topic as a table row.
    :param request: HttpRequest object
    :param topic_id: Topic object PK, when editing an existing topic
    :return: HttpResponse
    """
    from journal import forms as journal_forms  # Avoids circular import

    topic = None
    if topic_id:
        topic = get_object_or_404(
            journal_models.Topic,
            id=topic_id,
            journal=request.journal,
        )

    if request.method == "DELETE":
        if topic is None:
            raise Http404
        if topic.article_set.exists():
            response = render(
                request,
                "admin/core/partials/topics/topic_row.html",
                {"topic": topic},
            )
            return hx_show_message(
                response,
                _(
                    "You cannot remove a topic that contains articles."
                    " Remove articles from the topic if you want to delete it."
                ),
                level="warning",
            )
        topic.delete()
        return hx_show_message(HttpResponse(""), _("Topic deleted."))

    form = journal_forms.TopicForm(instance=topic)
    if request.method == "POST":
        form = journal_forms.TopicForm(request.POST, instance=topic)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.journal = request.journal
            topic.save()
            response = render(
                request,
                "admin/core/partials/topics/topic_row.html",
                {"topic": topic},
            )
            return hx_show_message(response, _("Topic saved."))

    template = "admin/core/partials/topics/topic_form.html"
    context = {
        "topic": topic,
        "topic_form": form,
    }
    return render(request, template, context)

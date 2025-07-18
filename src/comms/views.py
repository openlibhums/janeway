import urllib

from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.utils import translation

from comms import models, forms, logic
from core import models as core_models
from security.decorators import editor_user_required, file_user_required, has_request
from utils.decorators import GET_language_override
from utils.shared import language_override_redirect


@editor_user_required
@GET_language_override
def news(request):
    """
    Displays a list of news items for an editor user.

    :param request: HttpRequest object
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        new_items = models.NewsItem.objects.filter(
            content_type=request.model_content_type,
            object_id=request.site_type.pk,
        )

        if "delete" in request.POST:
            news_item_pk = request.POST.get("delete")
            item = get_object_or_404(
                models.NewsItem,
                pk=news_item_pk,
                content_type=request.model_content_type,
                object_id=request.site_type.pk,
            )
            item.delete()
            return redirect(
                reverse(
                    "core_manager_news",
                ),
            )

        template = "admin/comms/news_list.html"

        context = {
            "news_items": new_items,
        }

    return render(
        request,
        template,
        context,
    )


@editor_user_required
@GET_language_override
def manage_news(request, news_pk=None):
    """
    Handles the creation or editing of a NewsItem.

    If `news_pk` is provided, edits the existing NewsItem.
    Otherwise, creates a new one.

    :param request: HttpRequest object
    :param news_pk: Primary key of the NewsItem (optional)
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        if news_pk:
            news_item = get_object_or_404(
                models.NewsItem,
                pk=news_pk,
            )
            action = "edit"
        else:
            news_item = None
            action = "new"

        form = forms.NewsItemForm(
            instance=news_item,
            content_type=request.model_content_type,
            object_id=request.site_type.pk,
            posted_by=request.user,
        )

        new_file = None

        # Handle image deletion
        if "delete_image" in request.POST:
            delete_image_id = request.POST.get("delete_image")
            file = get_object_or_404(
                core_models.File,
                pk=delete_image_id,
            )

            if file.owner == request.user or request.user.is_staff:
                file.delete()
                messages.success(
                    request,
                    "Image deleted",
                )
            else:
                messages.warning(
                    request,
                    "Only the owner or staff can delete this image.",
                )
            return language_override_redirect(
                request,
                "core_manager_edit_news",
                kwargs={"news_pk": news_item.pk},
            )

        # Handle form submission
        if request.POST:
            form = forms.NewsItemForm(
                request.POST,
                instance=news_item,
                content_type=request.model_content_type,
                object_id=request.site_type.pk,
                posted_by=request.user,
            )

            if request.FILES:
                uploaded_file = request.FILES.get("image_file")
                new_file = logic.handle_uploaded_file(
                    request,
                    uploaded_file,
                )

                if isinstance(new_file, str):
                    # If the function returns a string it is an error message.
                    form.add_error(
                        "image_file",
                        new_file,
                    )
                    new_file = None

            if form.is_valid():
                news_item = form.save(
                    commit=True,
                )
                if new_file:
                    news_item.large_image_file = new_file
                    news_item.save()
                messages.success(
                    request,
                    "New item saved",
                )

                return language_override_redirect(
                    request,
                    "core_manager_edit_news",
                    kwargs={"news_pk": news_item.pk},
                )

        template = "admin/comms/manage_news.html"

        context = {
            "news_item": news_item,
            "action": action,
            "form": form,
        }

    return render(
        request,
        template,
        context,
    )


@has_request
@file_user_required
def serve_news_file(request, identifier_type, identifier, file_id):
    """Serves a news file (designed for use in the carousel).

    :param request: the request associated with this call
    :param identifier_type: the identifier type for the article
    :param identifier: the identifier for the article
    :param file_id: the file ID to serve
    :return: a streaming response of the requested file or 404
    """
    try:
        new_item = models.NewsItem.objects.get(
            content_type=request.model_content_type,
            object_id=request.site_type.pk,
            pk=identifier,
        )

        return new_item.serve_news_file()
    except models.NewsItem.DoesNotExist:
        raise Http404(
            f"No news item with ID {identifier} was found.",
        )


def news_list(request, tag=None, presswide=False):
    """
    Lists all a press or journal news items, and allows them to be filtered by tag
    :param request: HttpRequest object
    :param tag: a string matching a Tags.text attribute
    :param presswide: the string 'all' or False
    :return: HttpResponse object
    """

    news_objects = models.NewsItem.active_objects.all()

    if not presswide or request.model_content_type.model != "press":
        news_objects = news_objects.filter(
            content_type=request.model_content_type,
            object_id=request.site_type.id,
        )

    if tag:
        unquoted_tag = urllib.parse.unquote(tag)
        news_objects = news_objects.filter(
            tags__text=unquoted_tag,
        )
        tag = get_object_or_404(models.Tag, text=unquoted_tag)

    paginator = Paginator(news_objects, 12)
    page = request.GET.get("page", 1)

    try:
        news_items = paginator.page(page)
    except PageNotAnInteger:
        news_items = paginator.page(1)
    except EmptyPage:
        news_items = paginator.page(paginator.num_pages)

    all_tags = (
        models.Tag.objects.all()
        .annotate(Count("tags"))
        .order_by("-tags__count", "text")
    )

    if not request.journal:
        template = "press/core/news/index.html"
    else:
        template = "core/news/index.html"

    context = {
        "news_items": news_items,
        "tag": tag,
        "all_tags": all_tags,
    }

    return render(request, template, context)


def news_item(request, news_pk):
    """
    Renders a news item for public display.
    :param request: HttpRequest object
    :param news_pk: PK of a NewsItem object
    :return: HttpResponse object
    """
    item = get_object_or_404(
        models.NewsItem.objects.prefetch_related("tags"),
        pk=news_pk,
        content_type=request.model_content_type,
    )

    if request.journal:
        template = "core/news/item.html"
    else:
        template = "press/core/news/item.html"
    context = {
        "news_item": item,
    }

    return render(request, template, context)

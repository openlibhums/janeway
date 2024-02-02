import urllib

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count

from comms import models, forms
from core import files, logic as core_logic, models as core_models
from security.decorators import editor_user_required, file_user_required, has_request


@editor_user_required
def news(request):
    """
    Allows an editor user to add or delete news items.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    new_items = models.NewsItem.objects.filter(content_type=request.model_content_type,
                                               object_id=request.site_type.pk).order_by("sequence", "-start_display")
    form = forms.NewsItemForm()
    new_file = None

    if 'delete' in request.POST:
        news_item_pk = request.POST.get('delete')
        item = get_object_or_404(models.NewsItem,
                                 pk=news_item_pk,
                                 content_type=request.model_content_type,
                                 object_id=request.site_type.pk)
        item.delete()
        return redirect(reverse('core_manager_news'))

    if request.POST:
        form = forms.NewsItemForm(request.POST)

        if request.FILES:
            uploaded_file = request.FILES.get('image_file')

            if not files.guess_mime(uploaded_file.name) in files.IMAGE_MIMETYPES:
                form.add_error('image_file', 'File must be an image.')
            else:
                if request.model_content_type.name == 'journal':
                    new_file = files.save_file_to_journal(request, uploaded_file, 'News Item', 'News Item', public=True)
                    core_logic.resize_and_crop(new_file.journal_path(request.journal), [750, 324], 'middle')
                elif request.model_content_type.name == 'press':
                    new_file = files.save_file_to_press(request, uploaded_file, 'News Item', 'News Item', public=True)
                    core_logic.resize_and_crop(new_file.press_path(), [750, 324], 'middle')

        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.content_type = request.model_content_type
            new_item.object_id = request.site_type.pk
            new_item.posted_by = request.user
            new_item.posted = timezone.now()
            new_item.large_image_file = new_file
            new_item.save()

            return redirect(reverse('core_manager_news'))

    template = 'core/manager/news/index.html'
    context = {
        'news_items': new_items,
        'action': 'new',
        'form': form,
    }

    return render(request, template, context)


@editor_user_required
def edit_news(request, news_pk):
    """
    Allows an editor to edit an existing news item
    :param request: HttpRequest object
    :param news_pk: PK of an NewsItem object
    :return: HttpResponse object
    """
    new_items = models.NewsItem.objects.filter(content_type=request.model_content_type,
                                               object_id=request.site_type.pk).order_by('-posted')
    news_item = get_object_or_404(models.NewsItem, pk=news_pk)
    form = forms.NewsItemForm(instance=news_item)
    new_file = None

    if 'delete_image' in request.POST:
        delete_image_id = request.POST.get('delete_image')
        file = get_object_or_404(core_models.File, pk=delete_image_id)

        if file.owner == request.user or request.user.is_staff:
            file.delete()
            messages.add_message(request, messages.SUCCESS, 'Image deleted')
        else:
            messages.add_message(request, messages.WARNING, 'Only the owner or staff can delete this image.')

        return redirect(reverse('core_manager_edit_news', kwargs={'news_pk': news_item.pk}))

    if request.POST:
        form = forms.NewsItemForm(request.POST, instance=news_item)

        if request.FILES:
            uploaded_file = request.FILES.get('image_file')

            if request.model_content_type.name == 'journal':
                new_file = files.save_file_to_journal(request, uploaded_file, 'News Item', 'News Item', public=True)
                core_logic.resize_and_crop(new_file.journal_path(request.journal), [750, 324], 'middle')
            elif request.model_content_type.name == 'press':
                new_file = files.save_file_to_press(request, uploaded_file, 'News Item', 'News Item', public=True)
                core_logic.resize_and_crop(new_file.press_path(), [750, 324], 'middle')

        if form.is_valid():
            item = form.save(commit=False)
            if new_file:
                item.large_image_file = new_file
            item.save()
            return redirect(reverse('core_manager_news'))

    template = 'core/manager/news/index.html'
    context = {
        'news_item': news_item,
        'news_items': new_items,
        'action': 'edit',
        'form': form,
    }

    return render(request, template, context)


@has_request
@file_user_required
def serve_news_file(request, identifier_type, identifier, file_id):
    """ Serves a news file (designed for use in the carousel).

    :param request: the request associated with this call
    :param identifier_type: the identifier type for the article
    :param identifier: the identifier for the article
    :param file_id: the file ID to serve
    :return: a streaming response of the requested file or 404
    """

    new_item = models.NewsItem.objects.get(
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
        pk=identifier
    )

    return new_item.serve_news_file()


def news_list(request, tag=None, presswide=False):
    """
    Lists all a press or journal news items, and allows them to be filtered by tag
    :param request: HttpRequest object
    :param tag: a string matching a Tags.text attribute
    :param presswide: the string 'all' or False
    :return: HttpResponse object
    """

    news_objects = models.NewsItem.active_objects.all()

    if not presswide or request.model_content_type.model != 'press':
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
    page = request.GET.get('page', 1)

    try:
        news_items = paginator.page(page)
    except PageNotAnInteger:
        news_items = paginator.page(1)
    except EmptyPage:
        news_items = paginator.page(paginator.num_pages)

    all_tags = models.Tag.objects.all().annotate(
        Count('tags')
    ).order_by('-tags__count', 'text')

    if not request.journal:
        template = 'press/core/news/index.html'
    else:
        template = 'core/news/index.html'

    context = {
        'news_items': news_items,
        'tag': tag,
        'all_tags': all_tags,
    }

    return render(request, template, context)


def news_item(request, news_pk):
    """
    Renders a news item for public display.
    :param request: HttpRequest object
    :param news_pk: PK of a NewsItem object
    :return: HttpResponse object
    """
    item = get_object_or_404(models.NewsItem.objects.prefetch_related('tags'),
                             pk=news_pk,
                             content_type=request.model_content_type)

    if request.journal:
        template = 'core/news/item.html'
    else:
        template = 'press/core/news/item.html'
    context = {
        'news_item': item,
    }

    return render(request, template, context)

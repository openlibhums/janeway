__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.urls import reverse
from django.utils import translation
from django.views.decorators.http import require_POST

from security.decorators import editor_user_required
from cms import models, forms
from core import files
from core import models as core_models
from core.forms import XSLFileForm
from journal import models as journal_models
from utils import setting_handler
from utils.decorators import GET_language_override
from utils.shared import language_override_redirect, set_order


@editor_user_required
def index(request):
    """
    Displays a list of pages and the sites navigation structure.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    pages = models.Page.objects.filter(
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
    )
    top_nav_items = models.NavigationItem.objects.filter(
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
        top_level_nav__isnull=True,
    )
    collection_nav_items = None
    if request.journal:
        collection_nav_items = models.NavigationItem.get_issue_types_for_nav(
            request.journal)
    xsl_form = XSLFileForm()
    xsl_files = core_models.XSLFile.objects.filter(
        Q(journal=request.journal)|Q(journal__isnull=True)
    )

    if request.POST and 'delete' in request.POST:
        page_id = request.POST.get('delete')
        page = get_object_or_404(
            models.Page,
            pk=page_id,
            content_type=request.model_content_type,
            object_id=request.site_type.pk,
        )
        page.delete()
        return redirect(reverse('cms_index'))

    if request.POST and 'new_xsl' in request.POST:
        xsl_form = XSLFileForm(request.POST, request.FILES)
        if xsl_form.is_valid():
            xsl_form.save()
            messages.add_message(request, messages.INFO, "XSLT file has been uploaded.")
        else:
            messages.add_message(
                request, messages.ERROR,
                "Please correct the errors on the form and try again"
            )

        if 'clear' in request.POST:
            files.unlink_journal_file(request, file=None, xslt=True)
            request.journal.has_xslt = False
            request.journal.save()

    elif request.POST and 'change_xsl' in request.POST:
        xsl_file = get_object_or_404(core_models.XSLFile,
                pk=request.POST["change_xsl"])
        request.journal.xsl = xsl_file
        request.journal.save()

        return redirect(reverse('cms_index'))

    template = 'cms/index.html'
    context = {
        'journal': request.journal,
        'pages': pages,
        'top_nav_items': top_nav_items,
        'collection_nav_items': collection_nav_items,
        'xsl_form': xsl_form,
        'xsl_files': xsl_files,
    }

    return render(request, template, context)


def view_page(request, page_name):
    """
    Displays an individual CMS page using either the journal or press page template.
    :param request: HttpRequest object
    :param page_name: a string matching models.Page.page_name
    :return: HttpResponse object
    """
    current_page = get_object_or_404(models.Page, name=page_name,
                                     content_type=request.model_content_type,
                                     object_id=request.site_type.pk)

    if request.journal:
        template = 'cms/page.html'
    else:
        template = 'press/cms/page.html'
    context = {
        'page': current_page,
    }

    return render(request, template, context)


@editor_user_required
@GET_language_override
def page_manage(request, page_id=None):
    """
    Allows a staff member to add a new or edit an existing page.
    :param request: HttpRequest object
    :param page_id: pk of a Page object, not required
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        if page_id:
            page = get_object_or_404(models.Page, pk=page_id,
                                     content_type=request.model_content_type, object_id=request.site_type.pk)
            page_form = forms.PageForm(instance=page)
            edit = True
        else:
            page = None
            page_form = forms.PageForm()
            edit = False

        if request.POST:

            if page_id:
                page_form = forms.PageForm(request.POST, instance=page)
            else:
                page_form = forms.PageForm(request.POST)

            if page_form.is_valid():
                page = page_form.save(commit=False)
                page.content_type = request.model_content_type
                page.object_id = request.site_type.pk
                page.save()

                messages.add_message(request, messages.INFO, 'Page saved.')
                return language_override_redirect(
                    request,
                    'cms_page_edit',
                    {'page_id': page.pk},
                )

    template = 'cms/page_manage.html'
    context = {
        'page': page,
        'form': page_form,
        'edit': edit,
    }

    return render(request, template, context)


@editor_user_required
@GET_language_override
def nav(request, nav_id=None):
    """
    Allows a staff member to edit or add nav objects.
    :param request: HttpRequest object
    :param nav_id: pk of a Navigation object, not required
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        nav_to_edit = None
        if nav_id:
            nav_to_edit = get_object_or_404(models.NavigationItem, pk=nav_id)
        form = forms.NavForm(instance=nav_to_edit, request=request)

        top_nav_items = models.NavigationItem.objects.filter(
            content_type=request.model_content_type,
            object_id=request.site_type.pk,
            top_level_nav__isnull=True,
        )
        collection_nav_items = None
        if request.journal:
            collection_nav_items = models.NavigationItem.get_issue_types_for_nav(
                request.journal,
            )

        if request.POST.get('nav'):
            attr = request.POST.get('nav')
            setattr(request.journal, attr, not getattr(request.journal, attr))
            request.journal.save()
            return redirect(reverse('cms_nav'))

        elif "editorial_team" in request.POST:
            setting_handler.toggle_boolean_setting(
                setting_group_name="general",
                setting_name="enable_editorial_display",
                journal=request.journal,
            )

        elif 'keyword_list_page' in request.POST:
            setting_handler.toggle_boolean_setting(
                setting_group_name="general",
                setting_name="keyword_list_page",
                journal=request.journal,
            )

        elif "delete_nav" in request.POST:
            nav_to_delete = get_object_or_404(
                models.NavigationItem,
                pk=request.POST["delete_nav"],
                content_type=request.model_content_type,
                object_id=request.site_type.pk,
            )
            nav_to_delete.delete()
        elif "toggle_collection_nav" in request.POST:
            issue_type = get_object_or_404(
                journal_models.IssueType,
                journal=request.journal,
                pk=request.POST["toggle_collection_nav"],
            )
            models.NavigationItem.toggle_collection_nav(issue_type)

        if request.POST and 'edit_nav' in request.POST:
            form = forms.NavForm(
                request.POST, request=request, instance=nav_to_edit,
            )

            if form.is_valid():
                new_nav_item = form.save(commit=False)
                new_nav_item.content_type = request.model_content_type
                new_nav_item.object_id = request.site_type.pk
                new_nav_item.save()

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Nav Item Saved.',
                )

                return language_override_redirect(
                    request,
                    'cms_nav_edit',
                    {'nav_id': new_nav_item.pk},
                )

    template = 'cms/nav.html'
    context = {
        'form': form,
        'top_nav_items': top_nav_items,
        'collection_nav_items': collection_nav_items,
    }

    if request.journal:
        context['keyword_list_page'] = request.journal.get_setting(
            "general",
            "keyword_list_page",
        )
        context['enable_editorial_display'] = request.journal.get_setting(
            "general",
            "enable_editorial_display",
        )

    return render(request, template, context)


@editor_user_required
def submission_items(request):
    """
    Displays a list of a journals Submissions page items.
    """
    item_list = models.SubmissionItem.objects.filter(
        journal=request.journal,
    )
    if request.POST and 'delete' in request.POST:
        item_id = request.POST.get('delete')
        try:
            models.SubmissionItem.objects.get(
                pk=item_id,
                journal=request.journal,
            ).delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Item deleted.',
            )
        except models.SubmissionItem.DoesNotExist:
            messages.add_message(
                request,
                messages.ERROR,
                'No matching Submission Item found.',
            )

        return redirect(
            reverse('cms_submission_items'),
        )
    template = 'admin/cms/submission_item_list.html'
    context = {
        'item_list': item_list,
    }
    return render(request, template, context)


@editor_user_required
@GET_language_override
def edit_or_create_submission_item(request, item_id=None):
    with translation.override(request.override_language):
        if item_id:
            item = get_object_or_404(
                models.SubmissionItem,
                pk=item_id,
                journal=request.journal,
            )
        else:
            item = None

        form = forms.SubmissionItemForm(
            instance=item,
            journal=request.journal,
        )
        if request.POST:
            form = forms.SubmissionItemForm(
                request.POST,
                instance=item,
                journal=request.journal
            )
            if form.is_valid():
                saved_item = form.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'New item created.' if not item else 'Item updated.'
                )
                return language_override_redirect(
                    request,
                    'cms_edit_submission_item',
                    {'item_id': saved_item.pk}
                )

    template = 'admin/cms/submission_item_form.html'
    context = {
        'form': form,
        'item': item,
    }
    return render(request, template, context)


@require_POST
@editor_user_required
def order_submission_items(request):
    items = models.SubmissionItem.objects.filter(
        journal=request.journal,
    )
    set_order(
        items,
        'order',
        [int(item_pk) for item_pk in request.POST.getlist('item[]')]
    )
    return HttpResponse('Ok')

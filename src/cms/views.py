__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from security.decorators import editor_user_required
from cms import models, forms
from core import files
from core import models as core_models
from core.forms import XSLFileForm
from journal import models as journal_models


@editor_user_required
def index(request):
    """
    Displays a list of pages and the sites navigation structure.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    pages = models.Page.objects.filter(content_type=request.model_content_type, object_id=request.site_type.pk)
    top_nav_items = models.NavigationItem.objects.filter(content_type=request.model_content_type,
                                                         object_id=request.site_type.pk,
                                                         top_level_nav__isnull=True)
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
        page = get_object_or_404(models.Page, pk=page_id,
                                 content_type=request.model_content_type, object_id=request.site_type.pk)
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
def page_manage(request, page_id=None):
    """
    Allows a staff member to add a new or edit an existing page.
    :param request: HttpRequest object
    :param page_id: pk of a Page object, not required
    :return: HttpResponse object
    """
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
            return redirect(reverse('cms_index'))

    template = 'cms/page_manage.html'
    context = {
        'page': page,
        'form': page_form,
        'edit': edit,
    }

    return render(request, template, context)


@editor_user_required
def nav(request, nav_id=None):
    """
    Allows a staff member to edit or add nav objects.
    :param request: HttpRequest object
    :param nav_id: pk of a Navigation object, not required
    :return: HttpResponse object
    """
    if nav_id:
        nav_to_edit = get_object_or_404(models.NavigationItem, pk=nav_id)
        form = forms.NavForm(instance=nav_to_edit, request=request)
    else:
        nav_to_edit = None
        form = forms.NavForm(request=request)

    top_nav_items = models.NavigationItem.objects.filter(content_type=request.model_content_type,
                                                         object_id=request.site_type.pk,
                                                         top_level_nav__isnull=True)
    collection_nav_items = None
    if request.journal:
        collection_nav_items = models.NavigationItem.get_issue_types_for_nav(
            request.journal)

    if request.POST.get('nav'):
        attr = request.POST.get('nav')
        setattr(request.journal, attr, not getattr(request.journal, attr))
        request.journal.save()
        return redirect(reverse('cms_nav'))

    elif "delete_nav" in request.POST:
        nav_to_delete = get_object_or_404(
                models.NavigationItem,
                pk=request.POST["delete_nav"])
        nav_to_delete.delete()
    elif "toggle_collection_nav" in request.POST:
        issue_type = get_object_or_404(
            journal_models.IssueType,
            journal=request.journal,
            pk=request.POST["toggle_collection_nav"],
        )
        models.NavigationItem.toggle_collection_nav(issue_type)

    if request.POST:
        if nav_to_edit:
            form = forms.NavForm(request.POST, request=request, instance=nav_to_edit)
        else:
            form = forms.NavForm(request.POST, request=request)

        if form.is_valid():
            new_nav_item = form.save(commit=False)
            new_nav_item.content_type = request.model_content_type
            new_nav_item.object_id = request.site_type.pk
            new_nav_item.save()

            return redirect(reverse('cms_nav'))

    template = 'cms/nav.html'
    context = {
        'nav_item_to_edit': nav_to_edit,
        'form': form,
        'top_nav_items': top_nav_items,
        'collection_nav_items': collection_nav_items,
    }

    return render(request, template, context)

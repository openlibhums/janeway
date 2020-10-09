__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpResponse, Http404

from core import (
    files,
    models as core_models,
    plugin_loader,
    logic as core_logic,
)
from core.model_utils import merge_models
from journal import models as journal_models, views as journal_views, forms as journal_forms
from press import models as press_models, forms
from security.decorators import press_only
from submission import models as submission_models
from utils import install
from utils.logic import get_janeway_version


def index(request):
    """
    Press index page, displays blocks of HomepageElement objects
    :param request: HttpRequest object
    :return: HttpResponse object or journal_views.home if there is a request,journal
    """
    if request.journal is not None:
        # if there's a journal, then we render the _journal_ homepage, not the press
        return journal_views.home(request)

    homepage_elements, homepage_element_names = core_logic.get_homepage_elements(
        request,
    )

    template = "press/press_index.html"
    context = {
        'homepage_elements': homepage_elements,
    }

    # call all registered plugin block hooks to get relevant contexts
    for hook in settings.PLUGIN_HOOKS.get('yield_homepage_element_context', []):
        if hook.get('name') in homepage_element_names:
            hook_module = plugin_loader.import_module(hook.get('module'))
            function = getattr(hook_module, hook.get('function'))
            element_context = function(request, homepage_elements)

            for k, v in element_context.items():
                context[k] = v

    return render(request, template, context)


def journals(request):
    """
    Displays a filterable list of journals that are not marked as hidden
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    template = "press/press_journals.html"

    journal_objects = journal_models.Journal.objects.filter(
            hide_from_press=False,
            is_conference=False,
    ).order_by('sequence')

    context = {'journals': journal_objects}

    return render(request, template, context)


def conferences(request):
    """
    Displays a filterable list of conferences that are not marked as hidden
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    template = "press/press_journals.html"

    journal_objects = journal_models.Journal.objects.filter(
            hide_from_press=False,
            is_conference=True,
    ).order_by('sequence')

    context = {'journals': journal_objects}

    return render(request, template, context)


@staff_member_required
def manager_index(request):
    """
    This is an over-ride view that is returned by core_manager_index when there is no journal.
    :param request: django request
    :return: contextualised template
    """
    form = journal_forms.JournalForm()
    modal = None
    version = get_janeway_version()

    if request.POST:
        form = journal_forms.JournalForm(request.POST)
        modal = 'new_journal'
        if form.is_valid():
            new_journal = form.save(request=request)
            new_journal.sequence = request.press.next_journal_order()
            new_journal.save()
            call_command('install_plugins')
            install.update_license(new_journal)
            install.update_issue_types(new_journal)
            new_journal.setup_directory()
            return redirect("{0}?journal={1}".format(reverse('core_edit_settings_group', kwargs={'group': 'journal'}),
                                                     new_journal.pk))

    template = 'press/press_manager_index.html'
    context = {
        'journals': journal_models.Journal.objects.all().order_by('sequence'),
        'form': form,
        'modal': modal,
        'published_articles': submission_models.Article.objects.filter(
            stage=submission_models.STAGE_PUBLISHED
        ).select_related('journal')[:50],
        'version': version,
    }

    return render(request, template, context)


@staff_member_required
@press_only
def edit_press(request):
    """
    Staff members may edit the Press object.
    :param request: django request object
    :return: contextualised django template
    """

    press = request.press
    form = forms.PressForm(
        instance=press,
        initial={'press_logo': press.thumbnail_image}
    )

    if request.POST:
        form = forms.PressForm(request.POST, request.FILES, instance=press)
        if form.is_valid():
            form.save()

            if press.default_carousel_image:
                from core import logic as core_logic
                core_logic.resize_and_crop(press.default_carousel_image.path, [750, 324], 'middle')

            messages.add_message(request, messages.INFO, 'Press updated.')

            return redirect(reverse('press_edit_press'))

    template = 'press/edit_press.html'
    context = {
        'press': press,
        'form': form,
    }

    return render(request, template, context)


def serve_press_cover(request):
    """
    Returns the Press's cover file
    :param request: HttpRequest object
    :return: HttpStreamingResponse object with file
    """
    p = press_models.Press.get_press(request)

    if p.thumbnail_image:
        return files.serve_press_cover(request, p.thumbnail_image)
    else:
        raise Http404


@staff_member_required
def serve_press_file(request, file_id):
    """
    If a user is staff this view will serve a press file.
    :param request: HttpRequest
    :param file_id: core.File object pk
    :return: HttpStreamingResponse or Http404
    """
    file = get_object_or_404(core_models.File, pk=file_id)

    # If the file has an article_id the press should not serve it.
    # TODO: when untangling Files/Galleys this should be reviewed
    if file.article_id:
        raise Http404

    path_parts = ('press',)

    response = files.serve_any_file(
        request,
        file,
        False,
        path_parts=path_parts,
    )

    return response


@staff_member_required
def journal_order(request):
    """
    Takes a list of posted ids and sorts journals.
    :param request: request object
    :return: a json string
    """

    journals = journal_models.Journal.objects.all()

    ids = [int(_id) for _id in request.POST.getlist('journal[]')]

    for journal in journals:
        sequence = ids.index(journal.pk)
        journal_models.Journal.objects.filter(
            pk=journal.pk
        ).update(
            sequence=sequence
        )

    return HttpResponse('Thanks')


@staff_member_required
def journal_domain(request, journal_id):
    journal = get_object_or_404(journal_models.Journal, pk=journal_id)

    if request.POST:
        new_domain = request.POST.get('domain', None)

        if new_domain:
            journal.domain = new_domain
            journal.save()
            messages.add_message(request, messages.SUCCESS, 'Domain updated')
            return redirect(reverse('core_manager_index'))
        else:
            messages.add_message(request, messages.WARNING, 'No new domain supplied.')

    template = 'press/journal_domain.html'
    context = {
        'journal': journal,
    }

    return render(request, template, context)


@staff_member_required
def merge_users(request):
    users = core_models.Account.objects.all()
    if request.POST:
        from_id = request.POST["from"]
        to_id = request.POST["to"]
        if from_id == to_id:
            messages.add_message(
                request, messages.ERROR,
                "Can't merge a user with itself",
            )
        return redirect(reverse('merge_users'))

        try:
            from_acc = core_models.Account.objects.get(id=from_id)
            to_acc = core_models.Account.objects.get(id=to_id)
        except core_models.Account.DoesNotExist:
            messages.add_message(
                request, messages.ERROR,
                "Can't find users with ids %d, %d" % (from_id, to_id),
            )
        merge_models(from_acc, to_acc)
        messages.add_message(
            request, messages.INFO,
            "Merged %s into %s" % (from_acc.username, to_acc.username),
        )
        return redirect(reverse('merge_users'))

    template = "press/merge_users.html"
    context = {
        'users': users,
    }
    return render(request, template, context)


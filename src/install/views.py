__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse

from install import forms, logic
from core import files
from security.decorators import has_journal
from journal import models


@staff_member_required
def index(request):
    """
    Dislays a form allowing a user to upload an image file.
    :param request: HttpRequest object
    :return: HttpResponse or if request.POST: HttpRedirect
    """
    if request.POST:
        file = request.FILES.get('press_logo')
        file = files.save_file_to_press(request, file, 'Press Logo', '')
        request.press.thumbnail_image = file
        request.press.save()

        return redirect(reverse('install_index'))

    template = 'install/index.html'
    context = {}

    return render(request, template, context)


@staff_member_required
def journal(request):
    """
    Displays a journal's settings form for editing during the install process.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    settings_to_get = ['journal_name', 'journal_issn', 'publisher_name', 'publisher_url']
    initial_items = logic.get_initial_settings(request.journal, settings_to_get)

    attr_form = forms.JournalForm(instance=request.journal)
    sett_form = forms.JournalSettingsForm(initial=initial_items)

    if request.POST:
        attr_form = forms.JournalForm(request.POST, instance=request.journal)
        sett_form = forms.JournalSettingsForm(request.POST)

        if attr_form.is_valid() and sett_form.is_valid():
            attr_form.save()
            sett_form.save(request=request)

    template = 'install/journal.html'
    context = {
        'attr_form': attr_form,
        'sett_form': sett_form,
    }

    return render(request, template, context)


@staff_member_required
def next(request):
    """
    Displays a list of links of things a user should edit next after installing a new journal.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    template = 'install/next.html'
    context = {}

    return render(request, template, context)


@staff_member_required
def wizard_one(request, journal_id=None):
    """
    A set up wizard for Journals.
    """
    journal = None
    if journal_id:
        journal = get_object_or_404(
            models.Journal,
            pk=journal_id,
        )
    elif request.journal:
        journal = request.journal

    form = forms.CombinedJournalForm(
        instance=journal,
        setting_group='general',
        model_keys=['code', 'description'],
    )

    if request.POST:
        form = forms.CombinedJournalForm(
            request.POST,
            instance=journal,
            setting_group='general',
            model_keys=['code', 'description'],
        )
        if form.is_valid():
            form.save(commit=True)

    template = 'install/wizard/wizard.html'
    context = {
        'journal': journal,
        'step': 1,
        'help_template': 'install/wizard/help_1.html',
        'form': form,
    }
    return render(
        request,
        template,
        context
    )

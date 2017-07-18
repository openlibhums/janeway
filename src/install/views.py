__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from install import forms, logic
from core import files


@staff_member_required
def index(request):

    if request.POST:
        file = request.FILES.get('press_logo')
        file = files.save_file_to_press(request, file, 'Press Logo', '')
        request.press.thumbnail_image = file
        request.press.save()

    template = 'install/index.html'
    context = {}

    return render(request, template, context)


@staff_member_required
def journal(request):

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

    template = 'install/next.html'
    context = {}

    return render(request, template, context)

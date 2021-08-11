__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages

from core.homepage_elements.about import forms, plugin_settings
from security.decorators import editor_user_required
from utils.setting_handler import get_plugin_setting


@editor_user_required
def journal_description(request):

    title = get_plugin_setting(
        plugin_settings.get_self(),
        'about_title',
        request.journal,
        create=True,
    )

    description = request.journal.get_setting('general', 'journal_description')

    form = forms.AboutForm(
        initial={
            'title': title.value if title else 'About {name}'.format(
                name=request.journal.name,
            ),
            'description': description,
        }
    )

    if request.POST:
        form = forms.AboutForm(request.POST)
        if form.is_valid():
            form.save(request.journal)
            messages.add_message(request, messages.INFO, 'Settings updated.')
            return redirect(reverse('journal_description'))

    template = 'about_settings.html'
    context = {
        'form': form,
    }

    return render(request, template, context)

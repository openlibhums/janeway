__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages

from core.homepage_elements.html import forms
from utils import setting_handler, models
from security.decorators import editor_user_required


@editor_user_required
def html_settings(request):
    plugin = models.Plugin.objects.get(name='HTML')

    html_content = setting_handler.get_plugin_setting(
        plugin,
        'html_block_content',
        request.journal,
        create=True,
        pretty='HTML Block Content'
    ).value

    form = forms.HTMLForm(
        initial={
            'html_content': html_content,
        }
    )

    if request.POST:
        form = forms.HTMLForm(
            request.POST,
        )
        if form.is_valid():
            form.save(request.journal)
            messages.add_message(request, messages.INFO, 'HTML Block updated.')
            return redirect(reverse('home_settings_index'))

    template = 'html_settings.html'
    context = {
        'form': form,
    }

    return render(request, template, context)

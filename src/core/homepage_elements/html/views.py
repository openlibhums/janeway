__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import translation

from utils import setting_handler, models
from utils.decorators import GET_language_override
from security.decorators import editor_user_required

import forms


@GET_language_override
@editor_user_required
def html_settings(request):
    """
    Allows a staff member to add a new or edit an existing HTML block.
    :param request: HttpRequest object
    :return: HttpResponse object
    """

    plugin = models.Plugin.objects.get(name='HTML')

    html_setting = setting_handler.get_plugin_setting(
        plugin,
        'html_block_content',
        request.journal,
        create=True,
        pretty='HTML Block Content'
    )

    with translation.override(request.override_language):
        form = forms.HTMLBlockForm(html_setting=html_setting)

        if request.POST:
            form = forms.HTMLBlockForm(request.POST)
            if form.is_valid():
                form.save()

                messages.add_message(request, messages.INFO, 'HTML saved.')
            return redirect(reverse('home_settings_index'))

    template = 'html_settings.html'
    context = {
        'form': form,
    }

    return render(request, template, context)

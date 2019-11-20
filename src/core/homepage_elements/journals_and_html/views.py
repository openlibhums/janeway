__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import redirect, render, reverse
from django.contrib import messages

from security.decorators import editor_user_required
from core.homepage_elements.journals_and_html import forms
from press import models as press_models


@editor_user_required
def journals_and_html(request):
    html_setting, c = press_models.PressSetting.objects.get_or_create(
        press=request.press,
        name='journals_and_html_content',
    )
    form = forms.JournalsHTMLForm(
        instance=request.press,
        html_setting=html_setting
    )

    if request.POST:
        form = forms.JournalsHTMLForm(
            request.POST,
            instance=request.press,
            html_setting=html_setting,
        )
        if form.is_valid():
            form.save()
            form.save_m2m()

            messages.add_message(
                request,
                messages.SUCCESS,
                'Saved.'
            )

            return redirect(
                reverse(
                    'home_settings_index'
                )
            )

    template = 'journals_and_html.html'
    context = {
        'form': form,
    }

    return render(request, template, context)



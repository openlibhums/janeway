__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import redirect, render, reverse
from django.contrib import messages

from security.decorators import editor_user_required
from core.homepage_elements.journals import forms


@editor_user_required
def featured_journals(request):
    form = forms.FeaturedJournalsForm(instance=request.press)

    if request.POST:
        form = forms.FeaturedJournalsForm(request.POST, instance=request.press)
        if form.is_valid():
            form.save()
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

    template = 'featured_journals.html'
    context = {
        'form': form,
    }

    return render(request, template, context)



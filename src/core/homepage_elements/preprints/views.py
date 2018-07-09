__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import reverse
from django.shortcuts import redirect, render

from core.homepage_elements.preprints import forms
from security.decorators import editor_user_required


@editor_user_required
def preprints(request):

    form = forms.PreprintForm(instance=request.press)

    if request.POST:
        form = forms.PreprintForm(request.POST, instance=request.press)

        if form.is_valid():
            form.save()
            return redirect(reverse('preprints'))

    template = 'preprints.html'
    context = {
        'form': form,
    }

    return render(request, template, context)

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages


@staff_member_required
def journal_description(request):
    if request.POST:
        description = request.POST.get('description')
        request.journal.description = description
        request.journal.save()
        messages.add_message(request, messages.INFO, 'Description updated.')
        return redirect(reverse('journal_description'))

    template = 'about_settings.html'
    context = {}

    return render(request, template, context)

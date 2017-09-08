__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from cron import models, forms


@staff_member_required
def home(request):
    pass


@staff_member_required
def reminders(request):
    reminders = models.Reminder.objects.filter(journal=request.journal)

    form = forms.ReminderForm()

    if 'delete' in request.POST:
        reminder_id = request.POST.get('delete')
        reminder = get_object_or_404(models.Reminder, pk=reminder_id, journal=request.journal)
        reminder.delete()
        return redirect(reverse('cron_reminders'))

    if request.POST:
        form = forms.ReminderForm(request.POST)

        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.journal = request.journal
            reminder.save()
            return redirect(reverse('cron_reminders'))

    template = 'cron/reminders.html'
    context = {
        'reminders': reminders,
        'form': form,
    }

    return render(request, template, context)


@staff_member_required
def reminder(request, reminder_id):
    reminder = get_object_or_404(models.Reminder, journal=request.journal, pk=reminder_id)
    reminders = models.Reminder.objects.filter(journal=request.journal)

    form = forms.ReminderForm(instance=reminder)

    if request.POST:
        form = forms.ReminderForm(request.POST, instance=reminder)

        if form.is_valid():
            form.save()
            return redirect(reverse('cron_reminders'))

    template = 'cron/reminders.html'
    context = {
        'reminder': reminder,
        'reminders': reminders,
        'form': form,
    }

    return render(request, template, context)

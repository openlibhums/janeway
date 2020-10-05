__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.text import slugify

from cron import models, forms, logic
from utils import setting_handler
from security.decorators import editor_user_required


@staff_member_required
def home(request):
    """
    Does nothing
    :param request: HttpRequest object
    :return: pass
    """
    pass


@editor_user_required
def reminders_index(request):
    """
    Displays a list of Reminders and allows new ones to be created and existing ones to be deleted.
    :param request: HttpRequest object
    :return: HttpResponse or HttpRedirect if the template does not exist
    """
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
            reminder.template_name = slugify(reminder.template_name)
            reminder.save()

            check_template = logic.check_template_exists(request, reminder)

            if check_template:
                return redirect(reverse('cron_reminders'))
            else:
                return redirect(reverse('cron_create_template', kwargs={'reminder_id': reminder.pk,
                                                                        'template_name': reminder.template_name}))

    template = 'cron/reminders.html'
    context = {
        'reminders': reminders,
        'form': form,
    }

    return render(request, template, context)


@editor_user_required
def edit_reminder(request, reminder_id):
    """
    Allows for editing an existing Reminder object.
    :param request: HttpRequest object
    :param reminder_id: Reminder object PK
    :return: HttpResponse
    """
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


@editor_user_required
def create_template(request, reminder_id, template_name):
    """
    If a new Reminder.template doesn't exist, they are redirected here to create a new one.
    :param request: HttpRequest object
    :param reminder_id: Reminder object PK
    :param template_name: string, Reminder.template string
    :return: if POST HttpRedirect otherwise HttpResponse
    """
    reminder = get_object_or_404(models.Reminder, journal=request.journal, pk=reminder_id)

    if request.POST:
        template = request.POST.get('template')
        setting_handler.create_setting('email', template_name, 'rich-text', reminder.subject, '', is_translatable=True)
        setting_handler.save_setting('email', template_name, request.journal, template)

        return redirect(reverse('cron_reminders'))

    template = 'cron/create_template.html'
    context = {
        'reminder': reminder,
        'template_name': template_name,
    }

    return render(request, template, context)

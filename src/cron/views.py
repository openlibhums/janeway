__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from cron import models, forms, logic
from core import models as core_models
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

    if 'delete' in request.POST:
        reminder_id = request.POST.get('delete')
        reminder = get_object_or_404(models.Reminder, pk=reminder_id, journal=request.journal)
        reminder.delete()
        return redirect(reverse('cron_reminders'))

    template = 'cron/reminders.html'
    context = {
        'reminders': reminders,
    }

    return render(request, template, context)


@editor_user_required
def manage_reminder(request, reminder_id=None):
    """
    Allows for creating and editing of Reminder object.
    :param request: HttpRequest object
    :param reminder_id: Reminder object PK
    :return: HttpResponse
    """
    reminder = None
    if reminder_id:
        reminder = get_object_or_404(models.Reminder, journal=request.journal, pk=reminder_id)
    reminders = models.Reminder.objects.filter(journal=request.journal)

    form = forms.ReminderForm(
        instance=reminder,
        journal=request.journal,
    )

    if request.POST:
        form = forms.ReminderForm(
            request.POST,
            instance=reminder,
            journal=request.journal,
        )

        if form.is_valid():
            reminder = form.save()
            # Check if the template exists and redirect accordingly.
            check_template = logic.check_template_exists(request, reminder)
            if check_template:
                return redirect(reverse('cron_reminders'))
            else:
                return redirect(
                    reverse(
                        'cron_create_template',
                        kwargs={
                            'reminder_id': reminder.pk, 'template_name': reminder.template_name
                        }
                    )
                )

    template = 'cron/manage_reminder.html'
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

    try:
        text = setting_handler.get_setting('email', template_name, request.journal).value
    except core_models.Setting.DoesNotExist:
        text = ''

    if request.POST:
        template = request.POST.get('template')
        setting_handler.create_setting('email', template_name, 'rich-text', reminder.subject, '', is_translatable=True)
        setting_handler.save_setting('email', template_name, request.journal, template)

        return redirect(reverse('cron_reminders'))

    template = 'cron/create_template.html'
    context = {
        'reminder': reminder,
        'template_name': template_name,
        'text': text,
    }

    return render(request, template, context)

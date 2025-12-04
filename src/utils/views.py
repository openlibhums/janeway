__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils.decorators import method_decorator

from core import forms as core_forms, models as core_models
from core.views import GenericFacetedListView
from utils import logic, models
from security.decorators import editor_user_required, user_can_view_contact_message


@csrf_exempt
@require_POST
def mailgun_webhook(request):
    """
    Displays a list of reports.
    :param request: HttpRequest object
    :return: HttpResponse
    """

    message = logic.parse_mailgun_webhook(request.POST)
    return HttpResponse(message)


@method_decorator(editor_user_required, name="dispatch")
class ContactMessageListView(GenericFacetedListView):
    """
    Allows an contact person to view their contact messages.

    Should be subclassed at the site level for clarity.
    """

    model = models.LogEntry
    template_name = "admin/core/manager/contacts/message_list.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            context["contact_person"] = core_models.ContactPerson.objects.get(
                content_type=self.request.model_content_type,
                object_id=self.request.site_type.pk,
                account=self.request.user,
            )
        except core_models.ContactPerson.DoesNotExist:
            pass
        return context

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        queryset = queryset.filter(
            types="Contact Message",
            content_type=self.request.model_content_type,
            object_id=self.request.site_type.pk,
            addressee__email__iexact=self.request.user.email,
        )
        return queryset

    def get_facets(self):
        return {
            "q": {
                "type": "search",
                "field_label": "Search",
            },
            "date__gte": {
                "type": "date",
                "field_label": "Received after",
            },
            "date__lte": {
                "type": "date",
                "field_label": "Received before",
            },
        }

    def get_order_by_choices(self):
        return [
            ("-date", "Newest"),
            ("date", "Oldest"),
        ]


@user_can_view_contact_message
def contact_message(request, log_entry_id):
    log_entry = get_object_or_404(
        models.LogEntry,
        pk=log_entry_id,
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
    )
    context = {
        "log_entry": log_entry,
    }
    template = "admin/core/manager/contacts/message.html"
    return render(request, template, context)


@user_can_view_contact_message
def contact_message_delete(request, log_entry_id):
    next_url = request.GET.get("next", "")
    log_entry = get_object_or_404(
        models.LogEntry,
        pk=log_entry_id,
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
    )
    form = core_forms.ConfirmDeleteForm()
    if request.method == "POST":
        form = core_forms.ConfirmDeleteForm(request.POST)
        if form.is_valid():
            log_entry.delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Message deleted: %(subject)s" % {"subject": log_entry.email_subject},
            )
            if next_url:
                return redirect(next_url)
            else:
                return redirect(reverse("core_contact_messages"))

    context = {
        "log_entry": log_entry,
        "form": form,
        "thing_to_delete": log_entry.email_subject,
    }
    template = "admin/core/manager/contacts/message_confirm_delete.html"
    return render(request, template, context)

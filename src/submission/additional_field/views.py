from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from security.decorators import editor_user_required
from submission import forms, logic
from submission.forms import FieldForm
from submission.models import Field


@editor_user_required
def additional_fields_view(request):
    """
    Allows the editor to view and reorder submission fields.
    :param request: HttpRequest object
    :return: HttpResponse or HttpRedirect
    """
    fields: QuerySet[Field, Field] = logic.get_submission_fields(request)

    if request.POST:
        if "delete" in request.POST:
            logic.delete_field(request)
            return redirect(reverse("submission_fields"))

        elif "order[]" in request.POST:
            logic.order_fields(request, fields)
            return HttpResponse("Thanks")

    template = "admin/submission/manager/additional_fields/fields.html"
    context = {
        "fields": fields,
    }

    return render(request, template, context)


@editor_user_required
def edit_additional_field_view(request, field_id: str | None = None) -> HttpResponse:
    """
    Allows the editor to create, edit and delete new submission fields.
    :param request: HttpRequest object
    :param field_id: The ID of the field. Leave None to add a new field.
    :return: HttpResponse
    """
    field: Field = logic.get_current_field(request, field_id)
    form: FieldForm = forms.FieldForm(instance=field)

    if request.POST:
        if "save" in request.POST:
            form = forms.FieldForm(request.POST, instance=field)

            if form.is_valid():
                logic.save_field(request, form)
                return redirect(reverse("submission_fields"))

    template: str = (
        "admin/submission/manager/additional_fields/edit_additional_field.html"
    )
    context = {
        "field": field,
        "form": form,
    }

    return render(request, template, context)

from django.db.models import QuerySet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from security.decorators import editor_user_required
from submission import forms, logic
from submission.additional_field.forms import (
    FieldChoiceForm,
    FieldChoicesManagementForm,
)
from submission.forms import FieldForm
from submission.models import Field, FieldChoice


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
                field = logic.save_field(request, form)
                return redirect(
                    reverse("submission_fields_id", kwargs={"field_id": field.pk})
                )

    template: str = (
        "admin/submission/manager/additional_fields/edit_additional_field.html"
    )
    context = {
        "field": field,
        "form": form,
    }

    return render(request, template, context)


@editor_user_required
def manage_field_choices_view(request, field_id: str) -> HttpResponse:
    """
    Allows the editor to manage field choices for a select field.
    :param request: HttpRequest object
    :param field_id: The ID of the field.
    :return: HttpResponse
    """
    field: Field = get_object_or_404(Field, pk=field_id)

    # Only allow managing choices for select fields
    if field.kind != "select":
        return redirect(reverse("submission_fields"))

    choices = field.field_choices.all().order_by("order")

    if request.POST:
        if "save" in request.POST:
            # Handle saving all choices at once
            for choice in choices:
                real_value_key = f"real_value_{choice.id}"
                display_value_key = f"display_value_{choice.id}"

                if real_value_key in request.POST and display_value_key in request.POST:
                    choice.real_value = request.POST[real_value_key]
                    choice.display_value = request.POST[display_value_key]
                    choice.save()

            # Handle adding a new choice
            new_real_value = request.POST.get("new_real_value", "").strip()
            new_display_value = request.POST.get("new_display_value", "").strip()

            if new_real_value and new_display_value:
                FieldChoice.objects.create(
                    field=field,
                    real_value=new_real_value,
                    display_value=new_display_value,
                    order=choices.count(),
                )

            return redirect(
                reverse("manage_field_choices", kwargs={"field_id": field_id})
            )

        elif "delete" in request.POST:
            choice_id = request.POST.get("delete")
            try:
                choice = FieldChoice.objects.get(pk=choice_id, field=field)
                choice.delete()

                # Reorder remaining choices
                remaining_choices = field.field_choices.all().order_by("order")
                for i, choice in enumerate(remaining_choices):
                    choice.order = i
                    choice.save()
            except FieldChoice.DoesNotExist:
                pass

            return redirect(
                reverse("manage_field_choices", kwargs={"field_id": field_id})
            )

    template: str = (
        "admin/submission/manager/additional_fields/manage_field_choices.html"
    )
    context = {
        "field": field,
        "choices": choices,
    }

    return render(request, template, context)


@editor_user_required
@csrf_exempt
def reorder_field_choices_view(request, field_id: str) -> HttpResponse:
    """
    Allows the editor to reorder field choices for a select field.
    :param request: HttpRequest object
    :param field_id: The ID of the field.
    :return: JsonResponse
    """
    field: Field = get_object_or_404(Field, pk=field_id)

    # Only allow managing choices for select fields
    if field.kind != "select":
        return JsonResponse({"error": "Invalid field type"}, status=400)

    if request.POST:
        choice_ids = request.POST.getlist("choice[]")
        choice_ids = [int(_id) for _id in choice_ids]

        # Update the order of choices
        for i, choice_id in enumerate(choice_ids):
            try:
                choice = FieldChoice.objects.get(pk=choice_id, field=field)
                choice.order = i
                choice.save()
            except FieldChoice.DoesNotExist:
                pass

        return JsonResponse({"status": "success"})

    return JsonResponse({"error": "Invalid request"}, status=400)

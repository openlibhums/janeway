from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError

from core import forms, models, logic
from security.decorators import editor_or_journal_manager_required


@require_GET
@editor_or_journal_manager_required
def alt_text_form(request):
    try:
        content_type, object_id, file_path, obj = logic.resolve_alt_text_target(
            request,
        )
    except ValidationError:
        return HttpResponseBadRequest("Invalid model or pk")

    instance = models.AltText.objects.filter(
        content_type=content_type,
        object_id=object_id,
        file_path=file_path,
    ).first()

    form = forms.AltTextForm(
        instance=instance,
        content_type=content_type,
        object_id=object_id,
        file_path=file_path,
    )

    return render(
        request,
        "core/partials/alt_text/form.html",
        {
            "form": form,
            "object": obj,
            "file_path": file_path,
            "token": file_path,
        },
    )


@require_POST
@editor_or_journal_manager_required
def alt_text_submit(request):
    try:
        content_type, object_id, file_path, obj = logic.resolve_alt_text_target(request)
    except ValidationError:
        return HttpResponseBadRequest("Invalid model or pk")

    instance = models.AltText.objects.filter(
        content_type=content_type,
        object_id=object_id,
        file_path=file_path,
    ).first()

    form = forms.AltTextForm(
        request.POST,
        instance=instance,
        content_type=content_type,
        object_id=object_id,
        file_path=file_path,
    )

    if form.is_valid():
        form.save()
        return render(
            request,
            "core/partials/alt_text/edit_alt_text_button.html",
            {
                "object": obj,
                "token": file_path,
            },
        )

    return render(
        request,
        "core/partials/alt_text/form.html",
        {
            "form": form,
            "object": obj,
            "file_path": file_path,
        },
    )

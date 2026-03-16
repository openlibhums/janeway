import json

from django.core.cache import cache
from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError

from core import forms, models, logic
from security.decorators import editor_or_journal_manager_required


def hx_show_message(response, message, level="success"):
    """Set the HX-Trigger header to fire a showMessage toastr notification."""
    response["HX-Trigger"] = json.dumps(
        {"showMessage": {"type": level, "message": message}}
    )
    return response


JOURNAL_IMAGE_FIELDS = {
    "header_image",
    "default_cover_image",
    "default_large_image",
    "favicon",
    "press_image_override",
    "default_profile_image",
    "default_thumbnail",
}


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
        response = render(
            request,
            "core/partials/alt_text/edit_alt_text_button.html",
            {
                "object": obj,
                "token": file_path,
            },
        )
        hx_show_message(response, "Alt text saved.")
        return response

    return render(
        request,
        "core/partials/alt_text/form.html",
        {
            "form": form,
            "object": obj,
            "file_path": file_path,
        },
    )


@require_POST
@editor_or_journal_manager_required
def journal_image_upload(request, field_name):
    if field_name not in JOURNAL_IMAGE_FIELDS:
        return HttpResponseBadRequest("Invalid field name")

    if field_name == "default_thumbnail":
        logic.handle_default_thumbnail(request, request.journal, attr_form=None)
        cache.clear()
        request.journal.refresh_from_db()
    else:
        form = forms.JournalSingleImageForm(
            request.POST,
            request.FILES,
            instance=request.journal,
            field_name=field_name,
        )
        if not form.is_valid():
            return render(
                request,
                "admin/core/partials/journal_image/upload_field.html",
                {
                    "field_name": field_name,
                    "field": form[field_name],
                    "journal": request.journal,
                },
            )
        form.save()
        cache.clear()
        request.journal.refresh_from_db()

    response = _render_upload_field(request, field_name)
    return hx_show_message(response, "Image saved.")


def _render_upload_field(request, field_name):
    if field_name == "default_thumbnail":
        thumbnail_form = forms.JournalImageForm(instance=request.journal)
        field = thumbnail_form["default_thumbnail"]
    else:
        field = forms.JournalSingleImageForm(
            instance=request.journal,
            field_name=field_name,
        )[field_name]
    return render(
        request,
        "admin/core/partials/journal_image/upload_field.html",
        {
            "field_name": field_name,
            "field": field,
            "journal": request.journal,
        },
    )


@require_POST
@editor_or_journal_manager_required
def journal_image_remove(request, field_name):
    if field_name not in JOURNAL_IMAGE_FIELDS:
        return HttpResponseBadRequest("Invalid field name")

    if field_name == "default_thumbnail":
        if request.journal.thumbnail_image:
            request.journal.thumbnail_image.unlink_file(journal=request.journal)
            request.journal.thumbnail_image = None
            request.journal.save()
    else:
        setattr(request.journal, field_name, None)
        request.journal.save()

    cache.clear()
    request.journal.refresh_from_db()

    response = _render_upload_field(request, field_name)
    return hx_show_message(response, "Image removed.")

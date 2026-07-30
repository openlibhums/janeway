from core import logic as core_logic, files


def handle_uploaded_file(request, uploaded_file):
    """
    Handles file upload for news items, ensuring it's a valid image and
    saving it appropriately based on content type.

    :param request: HttpRequest object
    :param uploaded_file: Uploaded file object
    :return: File instance if valid, error string otherwise
    """
    if not uploaded_file:
        return None

    if files.guess_mime(uploaded_file.name) not in files.IMAGE_MIMETYPES:
        return "File must be an image."

    field_name = "Image file"
    filename = uploaded_file.name
    if request.model_content_type.name == "journal":
        new_file = files.save_file_to_journal(
            request,
            uploaded_file,
            "News Item",
            "News Item",
            public=True,
        )
        core_logic.resize_and_crop(
            new_file.journal_path(request.journal),
            field_name=field_name,
            original_filename=filename,
        )
    elif request.model_content_type.name == "press":
        new_file = files.save_file_to_press(
            request,
            uploaded_file,
            "News Item",
            "News Item",
            public=True,
        )
        core_logic.resize_and_crop(
            new_file.press_path(),
            field_name=field_name,
            original_filename=filename,
        )
    else:
        return "Invalid content type for file upload."

    return new_file

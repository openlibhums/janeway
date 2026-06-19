import json

from django.http import HttpResponse


def hx_redirect(url):
    """Return a response asking HTMX to perform a full-page redirect."""
    response = HttpResponse()
    response["HX-Redirect"] = url
    return response


def hx_show_message(response, message, level="success"):
    """Set the HX-Trigger header to fire a showMessage toastr notification."""
    response["HX-Trigger"] = json.dumps(
        {"showMessage": {"type": level, "message": message}}
    )
    return response

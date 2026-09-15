import json


def hx_show_message(response, message, level="success"):
    """Set the HX-Trigger header to fire a showMessage toastr notification."""
    response["HX-Trigger"] = json.dumps(
        {"showMessage": {"type": level, "message": message}}
    )
    return response

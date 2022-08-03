from django.forms import TextInput


class TagitWidget(TextInput):
    CSS_CLASS = "tagit-field"

    def __init__(self, attrs=None, *args, **kwargs):
        if not attrs:
            attrs = {}
        attrs["class"] = " ".join(("tagit-field", attrs.get("class", "")))
        super().__init__(attrs, *args, **kwargs)

    class Media:
        css = {"all": (
            "https://code.jquery.com/ui/1.11.0/themes/smoothness/jquery-ui.css",
        )}
        js = (
            "common/js/jq-ui.min.js",
            "common/js/tagit.js",
            "common/js/tagit-widget.js",
        )


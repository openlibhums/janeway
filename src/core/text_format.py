# Single source of truth for the reading-options bar: the reader-selectable
# fonts and colour schemes, plus the text-size step bounds. 

from django.utils.translation import gettext_lazy as _

# Global default text-size step bounds. 
DEFAULT_SIZE_BOUNDS = {"min": -3, "max": 6}

FONTS = {
    "default": {"label": _("Default Font"), "value": None},
    "sans-serif": {"label": _("Sans-serif"), "value": "Arial, Verdana, sans-serif"},
    "serif": {"label": _("Serif"), "value": 'Georgia, "Times New Roman", serif'},
    "monospace": {"label": _("Monospace"), "value": '"Courier New", monospace'},
    "opendyslexic": {
        "label": _("OpenDyslexic"),
        "value": '"OpenDyslexic", Verdana, sans-serif',
    },
}

COLOUR_SCHEMES = {
    "default": {"label": _("Default Colour"), "light": "#ffffff", "dark": "#1a1a1a"},
    "yellow": {"label": _("Yellow"), "light": "#F5F5DC", "dark": "#4c4c4c"},
    "blue": {"label": _("Blue"), "light": "#45E9F2", "dark": "#302F31"},
    "green": {"label": _("Green"), "light": "#00EA9A", "dark": "#003407"},
    "customise": {"label": _("Customise"), "light": None, "dark": None},
}


def size_bounds(font=None):
    """Resolve the text-size step bounds for a font.

    anticipating a future per-font bounds for the sizing.
    """
    entry = FONTS.get(font)
    if isinstance(entry, dict) and isinstance(entry.get("size"), dict):
        return entry["size"]
    return DEFAULT_SIZE_BOUNDS

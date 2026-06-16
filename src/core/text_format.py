# Single source of truth for the reading-options bar: the reader-selectable
# fonts and colour schemes, plus the text-size step bounds.

import re

from django.utils.translation import gettext_lazy as _

_HEX_COLOUR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

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
    # Custom-colour scheme. The full code path is intact (validation, paint
    # logic, JS custom state), but the bar template intentionally does NOT offer
    # "customise" in the colour menu for now — it is planned to return as an
    # accessible modal colour picker. See reading_options_bar.html.
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


def initial_region_colour_css(preferences):
    """CSS that paints .text-format-region in the reader's saved scheme."""
    if not isinstance(preferences, dict):
        return ""

    scheme = preferences.get("scheme", "default")
    darkmode = bool(preferences.get("darkmode"))
    if scheme == "customise":
        pair = preferences.get("custom") or {}
        light, dark = pair.get("light"), pair.get("dark")
    else:
        entry = COLOUR_SCHEMES.get(scheme) or {}
        light, dark = entry.get("light"), entry.get("dark")

    # No override for the default scheme in light mode (the theme's own colours
    # show); a scheme without a usable pair is treated as no colour.
    if (scheme == "default" and not darkmode) or not (light and dark):
        return ""

    background = dark if darkmode else light
    foreground = light if darkmode else dark
    # Defensive: only emit values we recognise as hex, so the resolved
    # preference can never inject arbitrary CSS.
    if not (_HEX_COLOUR_RE.match(background) and _HEX_COLOUR_RE.match(foreground)):
        return ""

    return (
        '.text-format-region,.text-format-region *:not([class*="fa"])'
        "{background-color:%s!important;color:%s!important}"
        ".text-format-region{padding:20px}"
    ) % (background, foreground)

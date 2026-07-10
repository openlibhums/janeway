# Reading Options Bar

The **Reading Options bar** is a control bar that lets a reader adjust how
text is displayed — e.g. **font**, **text size**, **colour scheme**.
On article pages it also carries the article-only options (e.g email author).

## Adding the *reading options bar* to a page template
This bar may be added to pages which extend a `base.html` template. 

1. **Include the bar** where you want the controls to appear.

```django
{% block reading_options_bar %}
    {% include "common/elements/journal/reading_options_bar.html" %}
{% endblock reading_options_bar %}
```

2. **Mark the elements** you want it to affect with the class `.text-format-region`.
This will affect all child-elements of the marked element. 
You may markup multiple elements on the same page.

The reading options are intended to assist with focusing on the main text on a page.
Do not markup the side content, `nav` or other *distractions* without good reason.

## Extending the reading text-format options

### Adding a new font

If the font is a web-safe stack (e.g. system serif/sans), only step 3 is required. 

1. Put the font files in `src/static/common/fonts/<family>/` (`.woff2`/`.woff`
   preferred; `.otf`/`.ttf` work too). Include the font's licence file.
2. Add an `@font-face` block to `src/static/common/css/text_readability.css`:

   ```css
   @font-face {
     font-family: "MyFont";
     src: url("../fonts/myfont/MyFont-Regular.woff2") format("woff2");
     font-weight: normal;
     font-style: normal;
     font-display: swap;
   }
   ```

   Add a second block with `font-weight: bold` for the bold face if you have one.

3. Add an entry to in `src/core/text_format.py`. The key is an arbitrary slug

   ```python
    FONTS = {
        # ...existing entries...
        "myfont": {"label": _("My Font"), "value": '"MyFont", Verdana, sans-serif'},
    }
    ```

### Adding a new colour scheme

A scheme is a **pair of two colours**. The Light/Dark toggle decides which is
background and which is foreground. So pick two colours with **good contrast against each 
other** or they will not be readable!

**For WCAG 2.2AA compliance go for 1:4.5 minimum.**

```python
COLOUR_SCHEMES = {
    # ...existing entries...
    "pink": {"label": _("Pink"), "light": "#ffd6e8", "dark": "#3a0b22"},

    # ... customise should remain as the final entry
    "customise": {"label": _("Customise"), "light": None, "dark": None},
}
```

#### Reserved colour scheme keys

- **`default`** is special-cased in `applyPreferences()`: in **Light** it applies
  *no* override (the genuine theme colours show); in **Dark** it applies a dark
  mode (`#1a1a1a` background / `#ffffff` text). Selecting `default` also resets
  the mode to Light and re-shows italics. Your new schemes do **not** get this
  special-casing — they always apply their pair.
- **`customise`** reads the two `<input type="color">` values via
  `setCustomLight` / `setCustomDark`; the Light/Dark swap applies to it too.

### Adding a new setting
Adding a brand-new *kind* of setting (not just another font or colour) is three
matching edits: 
- an update to the `reading_options_bar.html` template
- a field on the JS `state` object, 
- a validation branch in`clean_text_format_preferences()`
- tests to cover the new setting. If it's a toggle then it only needs to be added to the `TOGGLE_FLAGS` in `src/core/logic.py` and it will be tested with the other toggles.

## How preferences persist

A reader's choices  are stored **server-side** and restored on the next page load
as per the accessibility mode preference:

- **Logged-in readers** — on the `Account.text_format_preferences` JSON field.
- **Anonymous readers** — in the session. On login, a choice the reader made
  while anonymous is written back to their account (an untouched session leaves
  the account value standing).

The bar template seeds the stored values into the page as JSON
(`{{ text_format_preferences|json_script:"tf-preferences" }}`). The JS reads them
in `loadPreferences()` before the first apply, and `savePreferences()` POSTs the
whole `state` object back with a short wait so that rapid changes collapse into a single request, and failing silently if it doesn't succeed to the `save_text_format_preferences` endpoint.

### Validation 
The save endpoint runs every value through
`clean_text_format_preferences()` in `src/core/logic.py`, which **drops anything
it doesn't recognise**. Validation derives its allow-lists from the
`src/core/text_format.py` registry — the single source of truth.

Note: `serialiseState()` already sends every non-function property of `state`
automatically.
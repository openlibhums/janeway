# Reading Options Bar

## Adding the *reading options bar* to a template

The **Reading Options bar** is a sticky control bar that lets a reader adjust how
body text is displayed — **font**, **text size**, **italics on/off**, **colour
scheme** (with custom colours and a Light/Dark swap) — without changing the rest
of the page. On article pages it also carries the article-only options
(citation formats, email author, print).

On pages that load `reversable-links.js` (article pages), the bar also shows a
**highlight-on-jump** toggle. The draw-attention feature flashes a highlight on
the block a reader jumps to via an internal link; the toggle suppresses that
highlight colour (the scroll and focus jump are kept). The button is hidden on
pages where `drawUserAttention` is not defined, so it is only offered where it
does something.

### The two things you must do

Adding the bar is two steps:

1. **Include the bar** where you want the controls to appear.
2. **Mark the content** you want it to affect with the class `.text-format-region`.

That's it — the bar is a self-contained drop-in. It loads its own CSS and JS, so
you do **not** need to add anything to the template's `head` or `js` blocks.


## Extending the reading text-format options

### Adding a new font

Skip this if your font is a web-safe stack (e.g. system serif/sans). To bundle a
custom face:

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

### Register a new font 

Add an entry to in `src/core/text_format.py`. The key is an arbitrary slug

```python
FONTS = {
    # ...existing entries...
    "myfont": {"label": _("My Font"), "value": '"MyFont", Verdana, sans-serif'},
}
```

### Register a new colour scheme

A scheme is a **pair of two colours**. The Light/Dark toggle decides which is
background and which is foreground. So pick two colours with **good contrast against each 
other**, because each one serves as text in one of the two modes. 

**For WCAG 2.2AA compliance go for 1:4.5 minimum.**

```python
COLOUR_SCHEMES = {
    # ...existing entries...
    "pink": {"label": _("Pink"), "light": "#ffd6e8", "dark": "#3a0b22"},

    # ... customise should remain as the final entry
    "customise": {"label": _("Customise"), "light": None, "dark": None},
}
```

### Reserved scheme keys — do not remove

- **`default`** is special-cased in `applyPreferences()`: in **Light** it applies
  *no* override (the genuine theme colours show); in **Dark** it applies a dark
  mode (`#1a1a1a` background / `#ffffff` text). Selecting `default` also resets
  the mode to Light and re-shows italics. Your new schemes do **not** get this
  special-casing — they always apply their pair.
- **`customise`** reads the two `<input type="color">` values via
  `setCustomLight` / `setCustomDark`; the Light/Dark swap applies to it too.

---


## How preferences persist

A reader's choices (font, colour scheme, dark mode, italics, text size) are
stored **server-side** and restored on the next page load:

- **Logged-in readers** — on the `Account.text_format_preferences` JSON field.
- **Anonymous readers** — in the session. On login, a choice the reader made
  while anonymous is written back to their account (an untouched session leaves
  the account value standing).

The bar template seeds the stored values into the page as JSON
(`{{ text_format_preferences|json_script:"tf-preferences" }}`). The JS reads them
in `loadPreferences()` before the first apply, and `savePreferences()` POSTs the
whole `state` object back — debounced, best-effort — to the
`save_text_format_preferences` endpoint.

**Why this matters when extending:** the save endpoint runs every value through
`clean_text_format_preferences()` in `src/core/logic.py`, which **drops anything
it doesn't recognise**. Validation derives its allow-lists from the
`src/core/text_format.py` registry — the single source of truth — so a font or
scheme present in the registry persists automatically. The steps below show the
one registry edit that covers validation, the menu, and the JS.

Adding a brand-new *kind* of setting (not just another font or colour) is three
matching edits: 
- an update to the `reading_options_bar.html` template
- a field on the JS `state` object, 
- a validation branch in`clean_text_format_preferences()`

Note: `serialiseState()` already sends every non-function property of `state`
automatically.
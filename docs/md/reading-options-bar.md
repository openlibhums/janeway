# Reading Options Bar

## Adding the Reading Options bar to a template

The **Reading Options bar** is a sticky control bar that lets a reader adjust how
body text is displayed — **font**, **text size**, **italics on/off**, **colour
scheme** (with custom colours and a Light/Dark swap) — without changing the rest
of the page. On article pages it also carries the article-only options
(citation formats, email author, print).

### The two things you must do

Adding the bar is two steps:

1. **Include the bar** where you want the controls to appear.
2. **Mark the content** you want it to affect with the class `.text-format-region`.

That's it — the bar is a self-contained drop-in. It loads its own CSS and JS, so
you do **not** need to add anything to the template's `head` or `js` blocks.

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
matching edits: a field on the JS `state` object, a validation branch in
`clean_text_format_preferences()`, and nothing else on the wire —
`serialiseState()` already sends every non-function property of `state`
automatically.

## Extending the Reading text-format options

### Adding a font

#### 1. (Optional) Bundle a webfont

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

#### 2. Register the font (one registry edit)

Add an entry to `FONTS` in `src/core/text_format.py`. The key is an arbitrary
slug; the value is an object with a `label` (the name shown on the Font button,
wrapped in `gettext_lazy` as `_`) and a `value` — the CSS `font-family` stack,
which should always end with a generic family as a fallback (`None` means "use
the theme's own font").

```python
FONTS = {
    # ...existing entries...
    "myfont": {"label": _("My Font"), "value": '"MyFont", Verdana, sans-serif'},
}
```

That single edit feeds the menu, server-side validation, and the JS — the bar
loops the registry for its `<li>`s, `clean_text_format_preferences()` derives its
allow-list from it, and `text_readability.js` reads the (translated) labels and
font stacks from the `#tf-options` blob. There is nothing to add to the JS, the
template, or `core/logic.py`.

#### 3. Rebuild and test

Rebuild assets, open an article, pick the new font, and confirm:
- the body text changes font;
- **FontAwesome icons keep their glyphs** — the font rule deliberately excludes
  `[class*="fa"]` elements, so icons are unaffected (no action needed).

---

### Adding a preset colour scheme

A scheme is a **pair of two colours**. The Light/Dark toggle decides which is
background and which is foreground:

- **Light** → the `light` colour is the background, the `dark` colour is the text.
- **Dark** → swapped: the `dark` colour is the background, the `light` colour is
  the text.

So pick two colours with **good contrast against each other**, because each one
serves as text in one of the two modes. For WCAG 2.2AA compliance go for 1:4.5 minimum.

#### 1. Register the scheme (one registry edit)

Add an entry to `COLOUR_SCHEMES` in `src/core/text_format.py`, **before** the
`customise` entry (insertion order is the menu order, and `customise` stays
last). The key is an arbitrary slug; the value is an object with a `label`
(wrapped in `gettext_lazy` as `_`) and the scheme's two colours, `light` and
`dark`.

```python
COLOUR_SCHEMES = {
    # ...existing entries...
    "pink": {"label": _("Pink"), "light": "#ffd6e8", "dark": "#3a0b22"},
    "customise": {"label": _("Customise"), "light": None, "dark": None},
}
```

As with fonts, that one edit covers the menu, validation, and the JS data — there
is nothing to change in the template, `core/logic.py`, or
`text_readability.js`.

#### 2. Rebuild and test

Rebuild, then for the new scheme verify Light **and** Dark, and confirm the
nested cards / `.summary` panel and interactive buttons all recolour (the colour
rules apply to the region and every descendant).

#### Reserved scheme keys — do not remove

- **`default`** is special-cased in `applyPreferences()`: in **Light** it applies
  *no* override (the genuine theme colours show); in **Dark** it applies a dark
  mode (`#1a1a1a` background / `#ffffff` text). Selecting `default` also resets
  the mode to Light and re-shows italics. Your new schemes do **not** get this
  special-casing — they always apply their pair.
- **`customise`** reads the two `<input type="color">` values via
  `setCustomLight` / `setCustomDark`; the Light/Dark swap applies to it too.

---

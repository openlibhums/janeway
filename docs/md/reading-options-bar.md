# Reading Options Bar

## Adding the Reading Options bar to a template

The **Reading Options bar** is a sticky control bar that lets a reader adjust how
body text is displayed — **font**, **text size**, **italics on/off**, **colour
scheme** (with custom colours and a Light/Dark swap) — without changing the rest
of the page. On article pages it also carries the article-only options
(citation formats, email author, print).

This guide is for developers adding the bar to a **new template** — another theme's
article page, or a non-article page such as a CMS page.

> For adding a new **font** or **colour scheme** to the controls themselves, see
> `extending-text-format-options.md` instead. This guide only covers placing the
> bar and choosing what it targets.

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
it doesn't recognise**. A new font or colour scheme therefore needs its key added
to the matching server-side allow-list (`TEXT_FORMAT_FONTS` /
`TEXT_FORMAT_SCHEMES`) or it will apply *live* but never *persist*. The steps
below call this out.

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

#### 2. Register the font stack (JS)

Add an entry to `FONTS` in `src/static/common/js/text_readability.js`. The key
is an arbitrary slug; the value is an object with a `label` (the name shown on
the Font button) and a `value` — the CSS `font-family` stack, which should always
end with a generic family as a fallback (`null` means "use the theme's own
font").

#### 3. Allow the value server-side (Python)

So the choice persists (see **How preferences persist** above), add the same slug
to `TEXT_FORMAT_FONTS` in `src/core/logic.py`:

```python
TEXT_FORMAT_FONTS = {
    "default",
    "sans-serif",
    "serif",
    "monospace",
    "opendyslexic",
    "myfont",  # must match the FONTS key in text_readability.js
}
```

Skip this and the font still applies in the current page, but
`clean_text_format_preferences()` drops it on save, so it won't survive a reload
or login.

#### 4. Add the menu option (shared bar)

Add the font to the **Font** button menu in the shared
`reading_options_bar.html` — one edit covers all three themes. The
`state.setFont(...)` key must match the `FONTS` key; wrap the label in
`{% trans %}`:

```html
<li><button type="button" onclick="state.setFont('myfont'); event.stopPropagation();">{% trans 'My Font' %}</button></li>
```

#### 5. Rebuild and test

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

#### 1. Register the scheme (JS)

Add an entry to `COLOURS` in `src/static/common/js/text_readability.js`. The key
is an arbitrary slug; the value is an object with a `label` (the name shown on
the Colour scheme button) and the scheme's two colours, `light` and `dark`.

#### 2. Allow the value server-side (Python)

So the choice persists (see **How preferences persist** above), add the same slug
to `TEXT_FORMAT_SCHEMES` in `src/core/logic.py` (it sits beside
`TEXT_FORMAT_FONTS`):

```python
TEXT_FORMAT_SCHEMES = {"default", "yellow", "blue", "green", "customise", "pink"}
```

As with fonts, an unlisted scheme still applies live but is dropped on save.

#### 3. Add the menu option (shared bar)

Add the scheme to the **Colour scheme** button menu in the shared
`reading_options_bar.html`, **before** the `customise` option — one edit covers
all three themes. The `state.setScheme(...)` key must match the `COLOURS` key:

```html
<li><button type="button" onclick="state.setScheme('pink'); event.stopPropagation();">{% trans 'Pink' %}</button></li>
```

#### 4. Rebuild and test

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

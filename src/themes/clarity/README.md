# Clarity

A more modern theme for Janeway with a switchable colour palette system and accessibility improvements over the Clean theme.

## Installation

Clone or copy this theme into `src/themes/`, restart the server, then select **Clarity** under General Settings.

## Repository Support

Clarity includes repository (preprint) front-end templates. To enable them, add a local copy of the `REPOSITORY_THEMES` setting to your `settings.py` that includes `clarity`:

```python
REPOSITORY_THEMES = [
    "OLH",
    "material",
    "clarity",
]
```

## Colour Palettes

Clarity ships with four palettes:

| Palette | Description |
|---------|-------------|
| `evergreen` | Dark green header (default) |
| `ocean` | Dark blue header |
| `cardinal` | Dark red header |
| `paper` | White header with neutral accents, suited to journals with prominent logos |

### Changing the palette for a journal

Each journal can select its palette via **Manager > All Settings**, search for **Clarity Palette**, and set the value to one of the palette names above. The default is `evergreen`.

### Fine-grained customisation

For more control, use the custom styling plugin. It loads after the palette CSS so any declarations take precedence via the cascade.

**Override individual variables** to tweak colours without switching palette entirely:

```css
:root {
  --brand-primary: #your-colour;
  --brand-secondary: #your-colour;
  --header-bg: #your-colour;
}
```

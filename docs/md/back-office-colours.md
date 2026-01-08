# Back office colours

The Janeway back office has a minimal colour system with a primary colour, a secondary colour, an alert colour, and warm white and black shades for backgrounds and text.

The colours are set up in `src/static/admin/css/settings.css`. That file contains both named colours (e.g. `--clr-red`) and semantic variables (e.g. `--clr-alert`). Other files in `src/static/admin/css/` should call the semantic variables.

## Text and icons

Text and icons should generally be in black, or blue for links. Text on buttons should use the `-on-dark` semantic colour.

## Buttons

Primary buttons (blue) are the most important action on the page, like saving a form, creating an assignment when an article has arrived in a new workflow stage, or completing an action. There should only be one primary button per screen, in general.

Secondary buttons (dark tan) are other actions the user can take, but they are not the expected main action. Sometimes a page only contains secondary buttons, if there is no clear action that we want to emphasize over the others.

Warning or alert buttons (red) should be used only for destructive actions, like deleting a file or data. They should not be used for non-destructive actions like declining a request, rejecting a proposal, or cancelling an action, since these are often the normal business of running a journal, and belong to the secondary colour category. The warning/alert style is intentionally less vibrant, since the red colour would otherwise draw too much attention. There is no separation between warning and alert--they use the same colour.

For common use cases like saving, deleting, or sending, there are includable button templates in `templates/admin/elements`. These should be used wherever possible to keep the codebase smaller and more maintainable.

Some buttons have no style as such. For example, buttons within a `div.title-area` wrapper do not have any style applied. Links in the workflow actions box also just appear as black text with their respective icons. Icon-based links within tables are also not styled as buttons, but eventually these elements should be expanded to be more accessible with both icon and text.

## Callouts

The Bootstrap set of callouts should be used when a callout is desired (e.g. `bs-callout bs-callout-warning`). These have the most accessible style, with a single thick bar of colour down the left-hand side, and no change to the background that could affect text contrast.

## Toasts

The toastr widget that displays Django messages in the bottom right uses just two colours: primary and alert/warning.

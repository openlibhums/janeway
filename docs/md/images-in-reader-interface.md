# Images in reader interface

## List of image fields

- `comms.NewsItem.large_image_file`
- `submission.Article.large_image_file`
- `journal.Journal.default_large_image`
- `journal.Issue.large_image`
- `repository.Repository.hero_background`
- `press.Press.default_carousel_image`
- `press.Press.thumbnail_image`
- `journal.Journal.thumbnail_image`
- `submission.thumbnail_image_file`
- `journal.Journal.default_cover_image`
- `journal.Issue.cover_image`
- `journal.Journal.header_image`
- `repository.Repository.logo`
- `journal.Journal.press_image_override`
- `journal.Journal.favicon`
- `press.Press.favicon`
- `repository.Repository.favicon`
- `press.Press.secondary_image`
- `journal.Journal.default_profile_image`
- `core.Account.profile_image`
- `submission.Article.meta_image`
- `repository.Preprint.meta_image`

## The large image

The large image is a wide “hero” banner used across a number of pages in the reader interface.

### Where does it show up?

It is used at the top of item pages (article, issue, preprint, and news item), in some components that aggregate those items (carousel, featured articles, popular articles), and in one infrequently used list page--the **Collections** page.

### What fields hold large images?

These are the fields or setting values that are accessed for large images in various ways:

- `comms.NewsItem.large_image_file`
- `submission.Article.large_image_file`
- `journal.Journal.default_large_image`
- `journal.Issue.large_image`
- `repository.Repository.hero_background`
- `press.Press.default_carousel_image`
- `django.conf.settings.HERO_IMAGE_FALLBACK`

### How do the fallbacks work for large images?

Fallbacks or defaults can be set at the journal, issue, repository, press, and file-system levels, though not all fallbacks come into play at all site levels.

Here is how they play out for each page:

#### Article

1. `submission.Article.large_image_file`
2. `journal.Issue.large_image`
3. `journal.Journal.default_large_image`
4. `press.Press.default_carousel_image`
5. `django.conf.settings.HERO_IMAGE_FALLBACK`

The image is not displayed if the `disable_article_large_image` setting is on.

#### Issue

1. `journal.Issue.large_image`
2. `journal.Journal.default_large_image`
3. `press.Press.default_carousel_image`
4. `django.conf.settings.HERO_IMAGE_FALLBACK`

#### Collections

1. `journal.Issue.large_image`
2. `journal.Journal.default_large_image`
3. `press.Press.default_carousel_image`
4. `django.conf.settings.HERO_IMAGE_FALLBACK`

This is a seldom-accessed page that displays a list of collections, which are essentially issues. Rather than displaying issue thumbnails, it re-uses the large image files.

#### Preprint

1. `repository.Repository.hero_background`
2. `django.conf.settings.HERO_IMAGE_FALLBACK`

On the OLH theme, no large image is displayed on the preprint page.

The Clean theme does not support repositories.

#### Journal news item

1. `comms.NewsItem.large_image_file`
2. `journal.Journal.default_large_image`
3. `press.Press.default_carousel_image`
4. `django.conf.settings.HERO_IMAGE_FALLBACK`

#### Press news item

1. `comms.NewsItem.large_image_file`
2. `press.Press.default_carousel_image`
3. `django.conf.settings.HERO_IMAGE_FALLBACK`

The Material theme is not supported at the press level.

#### Carousel item

The fallback logic for each carousel item is identical to the fallbacks for that item’s page. For example, an issue in a carousel will have the same image that the issue page has.

The Material theme is not supported at the press level.

#### Featured articles and popular articles

Featured and popular article homepage elements have the same behavior as article pages.

### Is the large image cropped?

The large image is cropped to a maximum of 1500px wide by 648px tall, in preparation for display at up to 1100px wide (Clean), 1200px wide (OLH), or 1477px wide (Material). The top of the image is kept if it is taller than 648px.

The user is warned if they upload an image that is smaller than these dimensions. In the past, the image was cropped to 750px x 324px, so many databases will have smaller images. However, these images have always been forced into a display of up to 1100px to 1477px, so legacy images will not be any less clear than they have been from the beginning. Users can replace their legacy images with higher-resolution versions to get sharper display.

Whatever the original image’s dimensions, aspect ratios are preserved so that images do not appear skewed or stretched. The image height is adjusted depending on the viewport size, and the width is left alone, with the image centered and the vertical overflow hidden. As a result, smaller screens will generally get a narrower slice of the image (as long as the block is full-width).

### Does text overlap the large image?

In some themes, the large image is used as a backdrop for titles and other information, potentially creating accessibility issues. In the OLH theme, the same legacy linear gradient `.overlay` is kept to maximize contrast behind text, and in the Material theme, we keep the same a partially opaque box, `carousel-text-wrapper`. However, for the most accessible sites, journals should use the Clean theme, which does not place text in front of user-provided images.

### What CSS affects large images?

Each theme has its own version of a banner component: `.olh-banner`, `.material-banner`, and `.clean-banner`, as well as classes for the image itself and any heading that should be absolutely positioned (OLH and Material). These classes can be used across breakpoints and in partial-width blocks, as long as a grid width modifier like `col-md-12` has been applied to an ancestor element. The Clean-theme component has an additional option for explicit image height to support equal-height carousel items.

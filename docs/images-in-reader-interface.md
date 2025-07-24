# Images in reader interface

## Large images

The large image appears at the top of item pages (article, issue, preprint, and news item) and in some components that aggregate those items (carousel, featured articles, popular articles). Fallbacks or defaults can be set at the journal, repository, and press levels, though not all fallbacks come into play at all site levels.

The large image is cropped to a maximum of 1500px x 648px, in preparation for display at up to 1100px wide (Clean), 1200px wide (OLH), or 1477px wide (Material). The top of the image is kept. (On an earlier version of Janeway, the middle portion was kept.)

The user is warned if they upload an image that is less than these dimensions. In the past, the image was cropped to 750px x 324px, so many databases will have smaller images. However, these large images have always been forced into a display of up to 1100px to 1477px, so legacy images will not be any less clear than they have been from the beginning. Users can replace their legacy images with higher-resolution versions to get clearer display behavior.

Whatever the original image’s dimensions, aspect ratios are preserved so that images do not appear skewed or stretched. The image is set to 100% of its container width in all cases, with the vertical overflow hidden.

### CSS

The large image is set at full-width of the space provided for it by the layout. That’s the full width of the container on article pages, two thirds for the banner on the issue page, and one third in the featured articles homepage element.

```css
.clean-banner {
  max-height: min(var(--max-banner-height, 432px), 50vw);
}
.clean-banner .clean-banner-image {
  width: 100%;
}
```

The height is constrained to a max of `432px` on larger screens, or `50vw` on smaller screens.

The `--max-banner-height` variable allows us to replace `432px` with a smaller height in smaller spaces, such as in a column in the featured articles homepage element. Example from the clean theme:

```css
.col-md-4 .clean-banner {
  --max-banner-height: 144px;
}
```

### Related fields
- `comms.NewsItem.large_image_file`
- `submission.Article.large_image_file`
- `journal.Journal.default_large_image`
- `journal.Issue.large_image`
- `repository.Repository.hero_background`
- `press.Press.default_carousel_image`

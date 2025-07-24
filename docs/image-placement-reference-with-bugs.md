# Images in reader interface

## Large images

### Clean article page

Vertical constraint: `.card img { max-height: 250px; }`

Horizontal constraint: `.img-fluid { max-width: 100%; }`

Explicit sizing: `.card-img { width: 100%; }`

Mobile: The same rules apply, plus `.card img { min-height: 220px; object-fit: cover; }`

Filter: `.article-img { filter: brightness(50%); }`

### Clean carousel (journal home page)

Vertical constraint: `.card img { min-height: 500px; }`

Horizontal constraint: `.img-fluid { max-width: 100%; } .carousel-min { min-width: 100%; }`

Explicit sizing: None, but the constraints skew the image

Mobile: The same rules apply, so the image is compressed horizontally to be very tall and narrow. This feature is also not accessible on mobile, because the theme uses Bootstrap carousels, which have a caption that is hidden on small screens and cannot be unhidden, because it uses JavaScript that cannot be overridden.

Filter: `.article-img { filter: brightness(50%); }`

### Clean issue page

The same styles apply as on the Clean article page.

### OLH article page

Vertical constraint: `.article-orbit { max-height: 400px !important; }`

Horizontal constraint: `.orbit-image { max-width: 100%; }`

Explicit sizing: `.orbit-image { width: 100%; }`

Mobile: Image is not displayed

### Material article page

Vertical constraint: None

Horizontal constraint: None

Explicit sizing: `.card .card-image img { height: 260px; width: 100%; object-fit: cover; }`

Mobile: The same rules apply, so only the very center of the image is visible

### OLH carousel

Vertical constraint: None

Horizontal constraint: `.orbit-image { max-width: 100%; }`

Explicit sizing: `.orbit-image { width: 100%; }`

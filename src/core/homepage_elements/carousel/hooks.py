
def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(name='Carousel').exists():
        active_carousel, carousel_items = request.site_type.active_carousel
        return {'carousel_items': carousel_items,
                'carousel': active_carousel}
    else:
        return {}

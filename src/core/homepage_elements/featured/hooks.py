from core.homepage_elements.featured import models


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is None:
        return {}

    featured_element = homepage_elements.filter(
        configure_url="featured_articles_setup"
    ).first()

    if not featured_element:
        return {}

    featured_articles = models.FeaturedArticle.objects.filter(
        journal=request.journal
    )

    return {"featured_articles": featured_articles}

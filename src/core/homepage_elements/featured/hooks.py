from core.homepage_elements.featured import models


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(name='Featured Articles').exists():
        featured_articles = models.FeaturedArticle.objects.filter(journal=request.journal)

        return {'featured_articles': featured_articles}
    else:
        return {}

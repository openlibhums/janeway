from core.homepage_elements.featured import models, logic


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(
            name='Featured Articles',
    ).exists():

        most_downloaded, number, time = logic.get_popular_article_settings(
            request.journal
        )

        if most_downloaded:
            featured_articles = logic.get_most_popular_articles(
                request.journal,
                number,
                time,
            )
        else:
            featured_article_objects = models.FeaturedArticle.objects.filter(
                journal=request.journal,
            )
            featured_articles = [fa.article for fa in featured_article_objects]

        return {
            'featured_articles': featured_articles,
            'most_downloaded': most_downloaded,
        }
    else:
        return {}

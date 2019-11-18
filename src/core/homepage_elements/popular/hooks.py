from core.homepage_elements.popular import logic


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(
            name='Popular Articles',
    ).exists():

        most_popular, number, time = logic.get_popular_article_settings(
            request.journal
        )

        popular_articles = logic.get_most_popular_articles(
            request.journal,
            number,
            time,
        )

        return {
            'popular_articles': popular_articles,
            'most_popular': most_popular,
        }
    else:
        return {}

from django.db.models import Count

from submission import models as sm
from utils import setting_handler, function_cache
from core.homepage_elements.featured import plugin_settings


def get_popular_article_settings(journal):
    plugin = plugin_settings.get_self()

    try:
        most_downloaded = setting_handler.get_plugin_setting(
            plugin,
            'most_downloaded',
            journal,
        ).processed_value
    except IndexError:
        most_downloaded = False

    try:
        num_most_downloaded = setting_handler.get_plugin_setting(
            plugin,
            'num_most_downloaded',
            journal,
        ).processed_value
    except IndexError:
        num_most_downloaded = 0
    try:
        most_downloaded_time = setting_handler.get_plugin_setting(
            plugin,
            'most_downloaded_time',
            journal,
        ).processed_value
    except IndexError:
        most_downloaded_time = 'weekly'

    return most_downloaded, num_most_downloaded, most_downloaded_time


@function_cache.cache(600)
def get_most_popular_articles(journal, number, time):
    articles = sm.Article.objects.annotate(
        total=Count('articleaccess')
    ).order_by('-total')[:int(number)]

    for article in articles:
        print(article.title, article.total)

    return articles

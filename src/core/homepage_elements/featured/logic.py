from datetime import timedelta

from django.db.models import Count, OuterRef, Subquery
from django.utils import timezone

from submission import models as sm
from metrics import models
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


def calc_start_date(time):
    date_time = timezone.now()

    if time == 'weekly':
        delta = 7
    elif time == 'monthly':
        delta = 30
    else:
        delta = 365

    return date_time - timedelta(days=delta)


def get_most_popular_articles(journal, number, time):
    start_date = calc_start_date(time)
    print(start_date)

    accesses = models.ArticleAccess.objects.filter(
        article=OuterRef('pk'),
        accessed__gte=start_date,
    ).order_by().values('article')

    count_accesses = accesses.annotate(count=Count('*')).values('count')

    articles = sm.Article.objects.filter(
        journal=journal,
        stage=sm.STAGE_PUBLISHED,
    ).annotate(
        access_count=Subquery(count_accesses)
    ).order_by('-access_count')[:number]

    print(articles.query)

    return articles

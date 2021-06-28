from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from submission import models as sm
from utils import setting_handler
from core.homepage_elements.popular import plugin_settings


def get_popular_article_settings(journal):
    plugin = plugin_settings.get_self()

    try:
        most_popular = setting_handler.get_plugin_setting(
            plugin,
            'most_popular',
            journal,
        ).processed_value
    except AttributeError:
        most_popular = False

    try:
        num_most_popular = setting_handler.get_plugin_setting(
            plugin,
            'num_most_popular',
            journal,
        ).processed_value
    except AttributeError:
        num_most_popular = 0
    try:
        most_popular_time = setting_handler.get_plugin_setting(
            plugin,
            'most_popular_time',
            journal,
        ).processed_value
    except AttributeError:
        most_popular_time = 'weekly'

    return most_popular, num_most_popular, most_popular_time


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

    articles = sm.Article.objects.filter(
        journal=journal,
        stage=sm.STAGE_PUBLISHED,
        articleaccess__accessed__gte=start_date,
    ).annotate(
        access_count=Count("articleaccess")
    ).order_by('-access_count', 'title')[:number]

    return articles

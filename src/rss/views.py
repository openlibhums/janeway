__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils import timezone
from django.template.defaultfilters import striptags
from django.contrib.contenttypes.models import ContentType

from comms import models as comms_models
from core.templatetags.truncate import truncatesmart
from submission import models as submission_models
from repository import models as repo_models


class LatestNewsFeed(Feed):
    """RSS feed for Journal news articles"""
    link = "/news/"

    def get_object(self, request, *args, **kwargs):
        return request.journal if request.journal else request.press

    def title(self, obj):
        return "{} News Feed".format(obj.name)

    def description(self, obj):
        return "A feed of the 10 latest news items from {}".format(obj.name)

    def items(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return comms_models.NewsItem.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
        ).order_by('sequence')[:10]

    def item_title(self, item):
        return striptags(item.title)

    def item_description(self, item):
        return truncatesmart(item.body, 400)

    def item_author_name(self, item):
        if hasattr(item, 'posted_by'):
            return item.posted_by.full_name()
        else:
            return None

    def item_pubdate(self, item):
        return item.posted

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return reverse('core_news_item', args=[item.pk])


class LatestArticlesFeed(Feed):
    """RSS feed for journal articles"""
    link = "/articles/"

    def get_object(self, request, *args, **kwargs):
        return request.journal or request.press
    
    def title(self, obj):
        return "{} Article Feed".format(obj.name)

    def description(self, obj):
        return "A feed of the 10 latest articles from {}".format(obj.name)

    def items(self, obj):
        try:
            return submission_models.Article.objects.filter(
                date_published__lte=timezone.now(),
                journal=obj
            ).order_by('-date_published')[:10]
        except ValueError:
            return submission_models.Article.objects.filter(
                date_published__lte=timezone.now(),
                journal__press=obj,
                journal__hide_from_press=False,
            ).order_by('-date_published')[:10]

    def item_title(self, item):
        return striptags(item.title)

    def item_description(self, item):
        return truncatesmart(item.abstract, 400)

    def item_author_name(self, item):
        if hasattr(item, 'posted_by'):
            return item.correspondence_author.full_name()
        else:
            return None

    def item_pubdate(self, item):
        return item.date_published

    def feed_url(self, obj):
        return ""

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return item.url

class LatestPreprintsFeed(Feed):
    """RSS feed for preprints"""
    link = "/preprints/"

    def get_object(self, request, *args, **kwargs):
        return request.repository or request.press

    def title(self, obj):
        return "{} Preprint Feed".format(obj.name)

    def description(self, obj):
        return "A feed of the 10 latest preprints from {}".format(obj.name)

    def items(self, obj):
        return repo_models.Preprint.objects.filter(
            date_published__lte=timezone.now(),
            repository=obj
        ).order_by('-date_published')[:10]

    def item_title(self, item):
        return striptags(item.title)

    def item_description(self, item):
        return truncatesmart(item.abstract, 400)

    def item_author_name(self, item):
        if hasattr(item, 'owner'):
            return item.owner.full_name()
        else:
            return None

    def item_pubdate(self, item):
        return item.date_published

    def feed_url(self, obj):
        return ""

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return item.url
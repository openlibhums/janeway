__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db import models
from django.utils import timezone


def access_choices():
    return (
        ('download', 'Download'),
        ('view', 'View'),
    )


class ArticleAccess(models.Model):
    article = models.ForeignKey('submission.Article')
    type = models.CharField(max_length=20, choices=access_choices())
    identifier = models.CharField(max_length=200)
    accessed = models.DateTimeField(default=timezone.now)
    galley_type = models.CharField(max_length=200)

    def __str__(self):
        return '[{0}] - {1} at {2}'.format(self.identifier, self.article.title, self.accessed)


class HistoricArticleAccess(models.Model):
    article = models.OneToOneField('submission.Article')
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)

    def __str__(self):
        return 'Article {0}, Views: {1}, Downloads: {2}'.format(self.article.title, self.views, self.downloads)

    def add_one_view(self):
        views = self.views
        self.views = views + 1
        self.save()

    def add_one_download(self):
        downloads = self.downloads
        self.downloads = downloads + 1
        self.save()

    def remove_one_view(self):
        views = self.views
        self.views = views - 1
        self.save()

    def remove_one_download(self):
        downloads = self.downloads
        self.downloads = downloads - 1
        self.save()


def alt_metric_choices():
    return (
        ('twitter', 'Twitter'),
        ('crossref', 'Crossref'),
        ('datacite', 'DataCite'),
        ('reddit', 'Reddit'),
        ('reddit-links', 'Reddit Links'),
        ('hypothesis', 'Hypothesis'),
        ('newsfeed', 'News'),
        ('stackexchange', 'Stack Exchange'),
        ('web', 'Web'),
        ('wikipedia', 'Wikipedia'),
        ('wordpressdotcom', 'Wordpress'),

    )


class AltMetric(models.Model):
    article = models.ForeignKey('submission.Article')
    source = models.CharField(max_length=30, choices=alt_metric_choices())
    pid = models.TextField()
    timestamp = models.DateTimeField()

from itertools import chain
from operator import attrgetter

from django.apps import apps
from django.db import models
from django.utils.translation import ugettext_lazy as _

CAROUSEL_MODES = [
    ('off', _('Off')),
    ('latest', _('Latest Articles')),
    ('news', _('Latest News')),
    ('selected-articles', _('Selected Articles')),
    ('mixed', _('Latest Articles and News')),
    ('mixed-selected', _('Selected Articles and News')),
]


class Carousel(models.Model):
    mode = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        default='Latest',
        choices=CAROUSEL_MODES,
    )
    enabled = True

    exclude = models.BooleanField(
        help_text=_(
            "If enabled, the selectors below will behave as an exclusion list",
        ),
        default=False,
    )

    latest_articles = models.BooleanField(
        default=False,
        help_text="The carousel will display the latest published articles",
    )

    # these fields contains a custom list of articles and article-like carousel objects for Mixed and News modes
    articles = models.ManyToManyField(
        'submission.Article',
        blank=True,
        null=True,
        related_name='articles',
    )

    latest_news = models.BooleanField(
        default=False,
        help_text="The carousel will display the latest published news items",
    )

    # a selected news field
    news_articles = models.ManyToManyField(
        'comms.NewsItem',
        blank=True,
    )

    # article and news limits
    article_limit = models.IntegerField(
        verbose_name='Maximum Number of Articles to Show',
        default=3,
    )
    news_limit = models.IntegerField(
        verbose_name='Maximum Number of News Items to Show',
        default=0,
    )
    issues = models.ManyToManyField(
        'journal.issue',
        verbose_name=_("Issues and Collections"),
        blank=True,
    )

    current_issue = models.BooleanField(
        default=False,
        help_text="Always include the current issue",
    )

    def get_items(self):
        import core.logic as core_logic
        Article = apps.get_model("submission", "Article")
        Issue = apps.get_model("journal", "Issue")
        NewsItem = apps.get_model("comms", "NewsItem")

        articles = Article.objects.none()
        news = NewsItem.objects.none()
        issues = Issue.objects.none()

        if self.latest_articles:
            if hasattr(self, 'press'):
                articles |= core_logic.latest_articles(self, 'press')
            elif hasattr(self, 'journal'):
                articles |= core_logic.latest_articles(self, 'journal')
            if self.article_limit > 0:
                articles = articles[:self.article_limit]

        if self.articles.exists():
            if self.exclude:
                articles = articles.exclude(id__in=self.articles.all().values("id"))
            else:
                articles = chain(self.articles.all(), articles)

        if self.latest_news:
            if hasattr(self, 'press'):
                news |= core_logic.news_items(self, 'press')
            elif hasattr(self, 'journal'):
                news |= core_logic.news_items(self, 'journal')
            if self.news_limit > 0:
                news = news[:self.news_limit]

        if self.news_articles.exists():
            if self.exclude:
                news = news.exclude(pk__in=self.news_articles.all().values("id"))
            else:
                news = chain(self.news_articles.all(), news)

        if self.issues.exists():
            if self.exclude:
                issues = issues.exclude(pk__in=self.issues.all().values("id"))
            else:
                issues = chain(self.issues.all(), issues)

        return sorted(
            chain(articles, news, issues),
            key=attrgetter("date_published"),
            reverse=True,
        )


class CarouselObject(models.Model):
    large_image_file = models.ForeignKey('core.File', null=True, blank=True)
    url = models.CharField(max_length=5000, blank=True, null=True)
    title = models.CharField(max_length=300)
    index = models.IntegerField(default=1)
    articleID = models.ManyToManyField('submission.Article', null=True, blank=True)

    @property
    def local_url(self):
        return self.url

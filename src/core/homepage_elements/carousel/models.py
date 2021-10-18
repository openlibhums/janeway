from django.db import models
from django.utils.translation import ugettext_lazy as _


class Carousel(models.Model):

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


class CarouselObject(models.Model):
    large_image_file = models.ForeignKey('core.File', null=True, blank=True)
    url = models.CharField(max_length=5000, blank=True, null=True)
    title = models.CharField(max_length=300)
    index = models.IntegerField(default=1)
    articleID = models.ManyToManyField('submission.Article', null=True, blank=True)

    @property
    def local_url(self):
        return self.url

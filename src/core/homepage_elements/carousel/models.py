from django.db import models
from django.utils.translation import ugettext_lazy as _

# off = no carousel
# latest = latest 3 articles + custom set of CarouselObjects defined by user
# news = custom set of CarouselObjects defined by user
# selected articles = user picks which articles to display + custom set of CarouselObjects defined by user
CAROUSEL_MODES = [
    ('off', _('Off')),
    ('latest', _('Latest Articles')),
    ('news', _('News')),
    ('selected-articles', _('Selected Articles')),
    ('mixed', _('Latest Articles and News')),
    ('mixed-selected', _('Selected Articles and News')),
]


class Carousel(models.Model):
    mode = models.CharField(max_length=200, blank=False, null=False, default='Latest', choices=CAROUSEL_MODES)

    # if exclude is true and mode is Latest then articles marked as "excluded" will not be included
    exclude = models.BooleanField(default=False)

    # these fields contains a custom list of articles and article-like carousel objects for Mixed and News modes
    articles = models.ManyToManyField('submission.Article', blank=True, null=True, related_name='articles')

    # article and news limits
    article_limit = models.IntegerField(verbose_name='Maximum Number of Articles to Show', default=3)
    news_limit = models.IntegerField(verbose_name='Maximum Number of News Items to Show', default=0)

    @staticmethod
    def get_carousel_modes():
        return CAROUSEL_MODES


class CarouselObject(models.Model):
    large_image_file = models.ForeignKey('core.File', null=True, blank=True)
    url = models.CharField(max_length=5000, blank=True, null=True)
    title = models.CharField(max_length=300)
    index = models.IntegerField(default=1)
    articleID = models.ManyToManyField('submission.Article', null=True, blank=True)

    @property
    def local_url(self):
        return self.url

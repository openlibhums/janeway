from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from django.http import Http404

from core import files

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


class NewsItem(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='news_content_type', null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')

    title = models.CharField(max_length=500)
    body = models.TextField()
    posted = models.DateTimeField(default=timezone.now)
    posted_by = models.ForeignKey('core.Account', blank=True, null=True, on_delete=models.SET_NULL)

    start_display = models.DateField(default=timezone.now)
    end_display = models.DateField(blank=True, null=True)
    sequence = models.PositiveIntegerField(default=0)

    large_image_file = models.ForeignKey('core.File', null=True, blank=True, related_name='large_news_file',
                                         on_delete=models.SET_NULL)
    tags = models.ManyToManyField('Tag', related_name='tags')

    class Meta:
        ordering = ('-posted', 'title')

    @property
    def url(self):
        if self.content_type.name == 'press':
            secure = self.object.is_secure
        else:
            from utils import setting_handler
            secure = setting_handler.get_setting('general', 'is_secure', self.object).processed_value

        path = reverse('core_news_item', kwargs={'news_pk': self.pk})
        base = "http{0}://{1}".format(
            's' if secure else '',
            self.object.domain
        )
        return base + path

    @property
    def carousel_subtitle(self):
        return ""

    @property
    def carousel_title(self):
        return self.title

    @property
    def carousel_image_resolver(self):
        return 'news_file_download'

    def serve_news_file(self):
        if self.large_image_file:
            if self.content_type.name == 'press':
                return files.serve_file_to_browser(self.large_image_file.press_path(), self.large_image_file)
            else:
                return files.serve_file_to_browser(self.large_image_file.journal_path(self.object),
                                                   self.large_image_file)
        else:
            return Http404

    def set_tags(self, posted_tags):
        str_tags = [tag.text for tag in self.tags.all()]

        for tag in posted_tags:
            if tag not in str_tags:
                new_tag, c = Tag.objects.get_or_create(text=tag)
                self.tags.add(new_tag)

        for tag in str_tags:
            if tag not in posted_tags:
                tag = Tag.objects.get(text=tag)
                self.tags.remove(tag)

    def __str__(self):
        if self.posted_by:
            return '{0} posted by {1} on {2}'.format(self.title, self.posted_by.full_name, self.posted)
        else:
            return '{0} posted on {1}'.format(self.title, self.posted)


class Tag(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text

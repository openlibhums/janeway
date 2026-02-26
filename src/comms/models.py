from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from django.http import Http404
from django.utils.translation import gettext as _
from django.templatetags.static import static
from simple_history.models import HistoricalRecords
from django.utils.html import mark_safe

from core import files
from core.model_utils import JanewayBleachField, JanewayBleachCharField

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


class ActiveNewsItemManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                (
                    models.Q(start_display__lte=timezone.now())
                    | models.Q(start_display=None)
                )
                & (
                    models.Q(end_display__gte=timezone.now())
                    | models.Q(end_display=None)
                )
            )
        )


class NewsItem(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="news_content_type",
        null=True,
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey("content_type", "object_id")

    title = JanewayBleachCharField()
    body = JanewayBleachField()
    posted = models.DateTimeField(default=timezone.now)
    posted_by = models.ForeignKey(
        "core.Account", blank=True, null=True, on_delete=models.SET_NULL
    )

    start_display = models.DateField(
        default=timezone.now,
        help_text="If you want to schedule this news item in advance, select a date for it to be published. Otherwise, select today's date for it to publish immediately.",
    )

    end_display = models.DateField(
        blank=True,
        null=True,
        help_text="If you want your news item to appear for a limited time only, select a date for it to stop displaying.",
    )

    sequence = models.PositiveIntegerField(
        default=0,
        help_text="This controls the order of news items in relation to one another.",
    )

    large_image_file = models.ForeignKey(
        "core.File",
        null=True,
        blank=True,
        related_name="large_news_file",
        on_delete=models.SET_NULL,
        help_text="An image for the top of the news item page and the "
        "news list page. Note that it will be automatically "
        "cropped to 1500px x 648px, so wide images work best.",
    )
    tags = models.ManyToManyField("Tag", related_name="tags")
    custom_byline = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The name of this news item's author. If this section is left blank, the byline will credit you as the author.",
    )

    pinned = models.BooleanField(
        default=False,
        help_text="Tick this box to pin this item to the top of your news list.",
    )

    objects = models.Manager()
    active_objects = ActiveNewsItemManager()

    class Meta:
        ordering = ("pinned", "-posted", "title")

    @property
    def url(self):
        path = reverse("core_news_item", kwargs={"news_pk": self.pk})
        return self.object.site_url(path)

    @property
    def date_published(self):
        return self.posted

    @property
    def carousel_subtitle(self):
        return ""

    @property
    def carousel_title(self):
        return self.title

    @property
    def carousel_image_resolver(self):
        return "news_file_download"

    def serve_news_file(self):
        if self.large_image_file:
            if self.content_type.name == "press":
                return files.serve_file_to_browser(
                    self.large_image_file.press_path(), self.large_image_file
                )
            else:
                return files.serve_file_to_browser(
                    self.large_image_file.journal_path(self.object),
                    self.large_image_file,
                )
        else:
            return Http404

    def set_tags(self, posted_tags):
        str_tags = [tag.text for tag in self.tags.all()]

        for tag in posted_tags:
            if tag not in str_tags and tag != "":
                new_tag, c = Tag.objects.get_or_create(text=tag)
                self.tags.add(new_tag)

        for tag in str_tags:
            if tag not in posted_tags:
                tag = Tag.objects.get(text=tag)
                self.tags.remove(tag)

    def byline(self):
        if self.custom_byline:
            return _("Posted by {byline}").format(byline=self.custom_byline)
        elif self.posted_by:
            return _("Posted by {byline}").format(byline=self.posted_by.full_name())
        else:
            return ""

    def best_image_url(self):
        """
        Finds the best image url for a news item by checking:
        - If the item has a large image
        - If the item is for a press: if the press has a large image
        - If the item is for a journal: if the journal has a large image and if not,
        whether the journal's press has one.
        """
        path = None
        if self.large_image_file:
            path = reverse(
                "news_file_download",
                kwargs={
                    "identifier_type": "id",
                    "identifier": self.pk,
                    "file_id": self.large_image_file.pk,
                },
            )
        elif self.content_type.name == "press" and self.object.default_carousel_image:
            path = self.object.default_carousel_image.url
        elif self.content_type.name == "journal":
            if self.object.default_large_image:
                path = self.object.default_large_image.url
            elif self.object.press.default_carousel_image:
                path = self.object.press.default_carousel_image.url

        if path:
            return self.object.site_url(path=path)
        else:
            return static(settings.HERO_IMAGE_FALLBACK)

    @property
    def best_large_image_url(self):
        """
        An alias for best_image_url that is used by the carousel templates.
        """
        return self.best_image_url

    def __str__(self):
        if self.posted_by:
            return "{0} posted by {1} on {2}".format(
                self.title,
                self.posted_by.full_name(),
                self.posted,
            )
        else:
            return "{0} posted on {1}".format(
                mark_safe(self.title),
                self.posted,
            )


class Tag(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text

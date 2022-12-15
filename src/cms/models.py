__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from core.file_system import JanewayFileSystemStorage
from utils.logic import build_url_for_request


class Page(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='page_content', null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')

    name = models.CharField(
        max_length=300,
        help_text='The relative URL path to the page, using lowercase '
                  'letters and hyphens. For example, a page about '
                  'research integrity might be “research-integrity”.',
        verbose_name='Link',
    )
    display_name = models.CharField(
        max_length=100,
        help_text='Name of the page, in 100 characters or fewer, '
                  'displayed in the nav and in the top-level heading '
                  'on the page (e.g. “Research Integrity”).',
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text='The content of the page. For headings, we recommend '
                  'using the Style dropdown (looks like a wand) and '
                  'selecting a heading level from 2 to 6, as the display '
                  'name field occupies the place of heading level 1. '
                  'Note that copying and pasting from a word processor '
                  'can produce unwanted results, but you can use Remove '
                  'Font Style (looks like an eraser) to remove some '
                  'unwanted formatting. To edit the page as HTML, '
                  'turn on the Code View (<>).',
    )
    is_markdown = models.BooleanField(default=True)
    edited = models.DateTimeField(auto_now=timezone.now)

    def __str__(self):
        return u'{0} - {1}'.format(self.content_type, self.display_name)


class NavigationItem(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='nav_content', null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')

    link_name = models.CharField(
        max_length=100,
        help_text='The text that will appear in the nav bar '
                  '(e.g. “About” or “Research Integrity”)',
        verbose_name='Display name',
    )
    link = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='In most cases, this should be the the '
                  'relative URL path to the page. The '
                  'relative path is formed from 1) the '
                  'journal code (acronym or abbreviation) '
                  'if your journal homepage URL ends with '
                  'the journal code, 2) the word “site”, and '
                  '3) whatever you put into the Link field for '
                  'the corresponding page. For example, '
                  'to link to a custom page you created, '
                  'if the journal homepage URL is “example.com/abc”, '
                  'and you put “research-integrity” in the Link field '
                  'for the page, then the Link field for the nav item '
                  'should be “abc/site/research-integrity”. For top-level '
                  'nav items that should not also appear as sub-nav '
                  'items (under themselves), leave the Link field empty. '
                  'For external links, it should be an absolute URL.',
    )
    is_external = models.BooleanField(
        default=False,
        help_text='Whether the link is to an external website.',
    )
    sequence = models.IntegerField(
        default=99,
        help_text='The order in which custom nav items appear relative '
                  'to other custom nav items. Note that fixed (default) '
                  'nav items do not have a sequence field, so you have '
                  'to replace them with custom elements to change their '
                  'order.',
    )
    page = models.ForeignKey(Page, blank=True, null=True)
    has_sub_nav = models.BooleanField(
        default=False,
        verbose_name="Has sub navigation",
        help_text='Whether this item has sub-nav items under it.',
    )
    top_level_nav = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        verbose_name="Top-level nav item",
        help_text='If this is a sub-nav item, which top-level '
                  'item should it go under?',
    )

    class Meta:
        ordering = ('sequence',)

    def __str__(self):
        return self.link_name

    def sub_nav_items(self):
        return NavigationItem.objects.filter(top_level_nav=self)

    @property
    def build_url_for_request(self):
        if self.is_external:
            return self.link
        else:
            return build_url_for_request(path=self.link)

    @property
    def url(self):
        #alias for backwards compatibility with templates
        if self.link:
            return self.build_url_for_request
        return ''

    @classmethod
    def toggle_collection_nav(cls, issue_type):
        """Toggles a nav item for the given issue_type
        :param `journal.models.IssueType` issue_type: The issue type to toggle
        """

        defaults = {
            "link": "/collections/%s" % (issue_type.code),
        }
        content_type = ContentType.objects.get_for_model(issue_type.journal)

        nav, created = cls.objects.get_or_create(
            content_type=content_type,
            object_id=issue_type.journal.pk,
            link_name=issue_type.plural_name,
            defaults=defaults,
        )

        if not created:
            nav.delete()

    @classmethod
    def get_issue_types_for_nav(cls, journal):
        for issue_type in journal.issuetype_set.filter(
            ~Q(code="issue") # Issues have their own navigation
        ):
            content_type = ContentType.objects.get_for_model(
                issue_type.journal)
            if not cls.objects.filter(
                content_type=content_type,
                object_id=issue_type.journal.pk,
                link_name=issue_type.plural_name,
            ).exists():
                yield issue_type


class SubmissionItem(models.Model):
    """
    Model containing information to render the Submission page.
    SubmissionItems is registered for translation in cms.translation.
    """
    journal = models.ForeignKey('journal.Journal')
    title = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=99)
    existing_setting = models.ForeignKey('core.Setting', blank=True, null=True)

    class Meta:
        ordering = ('order', 'title')
        unique_together = (('journal', 'existing_setting'), ('journal', 'title'))

    def get_display_text(self):
        if self.existing_setting:
            return self.journal.get_setting(
                self.existing_setting.group.name,
                self.existing_setting.name,
            )
        else:
            return self.text

    def __str__(self):
        return "{journal} {title} - {setting}".format(
            journal=self.journal,
            title=self.title,
            setting=self.existing_setting,
        )


def upload_to_media_files(instance, filename):
    if instance.journal:
        return "journals/{}/{}".format(instance.journal.pk, filename)
    else:
        return "press/{}".format(filename)


class MediaFile(models.Model):
    label = models.CharField(max_length=255)
    file = models.FileField(
        upload_to=upload_to_media_files,
        storage=JanewayFileSystemStorage())
    journal = models.ForeignKey(
        'journal.Journal',
        null=True,
        blank=True,
    )
    uploaded = models.DateTimeField(
        default=timezone.now,
    )

    def unlink(self):
        try:
            os.unlink(
                self.file.path,
            )
        except FileNotFoundError:
            pass

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def link(self):
        return build_url_for_request(
            path=self.file.url,
        )

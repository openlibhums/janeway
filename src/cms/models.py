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
from core.model_utils import JanewayBleachField
from utils.logic import build_url_for_request


class Page(models.Model):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="page_content", null=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey("content_type", "object_id")

    name = models.CharField(
        max_length=300,
        help_text="The relative URL path to the page. This will appear after the slash (/) at the end of your journal's main URL in the link to this page. It cannot contain any capital letters, spaces or special characters.",
        verbose_name="Link",
    )
    display_name = models.CharField(
        max_length=100,
        help_text="The page title. This will display in the navigation bar and as the heading on your page. 100 characters maximum.",
    )
    template = models.CharField(
        blank=True,
        max_length=100,
        help_text="The custom template to use instead of the content field.",
    )
    content = JanewayBleachField(
        null=True,
        blank=True,
        help_text="The content of your page. If you are copying and pasting this content from a word processor, you may need to use the 'remove formatting' tool or paste without formatting and then format as needed using this editor. For any headings, we recommend using heading level 2 or below, as the page display name will be classed as heading 1. You can access different heading levels by clicking 'Format' and going to 'Blocks'. To edit the page as HTML, "
        "turn on the code view (<>).",
    )
    is_markdown = models.BooleanField(default=True)
    edited = models.DateTimeField(auto_now=timezone.now)
    display_toc = models.BooleanField(
        default=False,
        help_text="Tick this box to enable a sidebar showing a table of contents for your page based on the headers you have used.",
        verbose_name="Display table of contents",
    )

    # history = HistoricalRecords() is defined in cms.translation
    # for compatibility with django-modeltranslation

    def __str__(self):
        return "{0} - {1}".format(self.content_type, self.display_name)


class NavigationItem(models.Model):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="nav_content", null=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey("content_type", "object_id")

    link_name = models.CharField(
        max_length=100,
        help_text="The page title as it will display in the navigation bar.",
        verbose_name="Display name",
    )
    link = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="In most cases, this should be the the "
        "relative URL path to the page. The "
        "relative path is formed from 1) the "
        "journal code (acronym or abbreviation) "
        "if your journal homepage URL ends with "
        "the journal code, 2) the word “site”, and "
        "3) whatever you put into the Link field for "
        "the corresponding page. For example, "
        "to link to a custom page you created, "
        "if the journal homepage URL is “example.com/abc”, "
        "and you put “research-integrity” in the Link field "
        "for the page, then the Link field for the nav item "
        "should be “abc/site/research-integrity”. For top-level "
        "nav items that should not also appear as sub-nav "
        "items (under themselves), leave the Link field empty. "
        "For external links, it should be an absolute URL.",
    )
    is_external = models.BooleanField(
        default=False,
        help_text="Tick this box if you are linking to an external web page.",
    )
    sequence = models.IntegerField(
        default=99,
        help_text="The order in which custom nav items appear relative "
        "to other custom nav items. Note that fixed (default) "
        "nav items do not have a sequence field, so you have "
        "to replace them with custom elements to change their "
        "order.",
    )
    page = models.ForeignKey(
        Page,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    has_sub_nav = models.BooleanField(
        default=False,
        verbose_name="Has sub navigation",
        help_text="Tick this box if you want to create a drop-down in your navigation bar from this item.",
    )
    top_level_nav = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        verbose_name="Top-level nav item",
        help_text="If you want this to fall under an existing drop-down in your navigation bar, select which one it should fall under.",
        on_delete=models.CASCADE,
    )
    for_footer = models.BooleanField(
        default=False,
        help_text="Whether this item should appear in the footer. "
        "Not implemented for all themes.",
    )
    extend_to_journals = models.BooleanField(
        default=False,
        help_text="Whether this item should be "
        "extended to journal websites. "
        "Only implemented for footer links.",
    )

    class Meta:
        ordering = ("sequence",)
        constraints = [
            models.CheckConstraint(
                check=(Q(("link__isnull", True)) & Q(("has_sub_nav", True)))
                | (Q(("link__isnull", False)) & Q(("has_sub_nav", False)))
                | (Q(("link__isnull", True)) & Q(("has_sub_nav", False))),
                name="nav_item_has_either_link_or_sub_nav",
                violation_error_message="There cannot be both a link and a "
                "sub navigation.",
            ),
        ]

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
        # alias for backwards compatibility with templates
        if self.link:
            return self.build_url_for_request
        return ""

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
            ~Q(code="issue")  # Issues have their own navigation
        ):
            content_type = ContentType.objects.get_for_model(issue_type.journal)
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

    journal = models.ForeignKey(
        "journal.Journal",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    text = JanewayBleachField(blank=True, null=True)
    order = models.IntegerField(default=99)
    existing_setting = models.ForeignKey(
        "core.Setting",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ("order", "title")
        unique_together = (("journal", "existing_setting"), ("journal", "title"))

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
        upload_to=upload_to_media_files, storage=JanewayFileSystemStorage()
    )
    journal = models.ForeignKey(
        "journal.Journal",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
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

    def __str__(self):
        return self.file.path

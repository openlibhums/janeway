__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import datetime
from itertools import chain
from operator import itemgetter
import collections
import uuid
import os
import re

from django.conf import settings
from django.db import models, transaction
from django.db.models import OuterRef, Subquery, Value
from django.db.models.signals import post_save, m2m_changed
from django.utils.safestring import mark_safe
from django.dispatch import receiver
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.functional import cached_property
from django.utils.translation import gettext

from core import (
        files,
        models as core_models,
        workflow,
)
from core.file_system import JanewayFileSystemStorage
from core.model_utils import (
    AbstractSiteModel,
    SVGImageField,
    AbstractLastModifiedModel,
    JanewayBleachField,
)
from press import models as press_models
from submission import models as submission_models
from utils import setting_handler, logic, install
from utils.function_cache import cache, mutable_cached_property
from utils.logger import get_logger
from review import models as review_models

logger = get_logger(__name__)

# Issue types
# Use "Issue" for regular issues (rolling or periodic)
# Use "Collection" for special collections
ISSUE_TYPES = [
    ('Issue', 'Issue'),
    ('Collection', 'Collection'),
]

fs = JanewayFileSystemStorage()


def cover_images_upload_path(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "cover_images/"
    return os.path.join(path, filename)


def default_xsl():
    return core_models.XSLFile.objects.get(
            label=settings.DEFAULT_XSL_FILE_LABEL).pk


def issue_large_image_path(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "issues/{0}".format(instance.pk)
    return os.path.join(path, filename)


class Journal(AbstractSiteModel):
    code = models.CharField(max_length=40, unique=True, help_text=gettext(
        'Short acronym for the journal. Used as part of the journal URL'
        'in path mode and to uniquely identify the journal'
    ))
    current_issue = models.ForeignKey('Issue', related_name='current_issue', null=True, blank=True,
                                      on_delete=models.SET_NULL)
    carousel = models.OneToOneField(
        'carousel.Carousel',
        related_name='journal',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    thumbnail_image = models.ForeignKey(
        'core.File',
        null=True,
        blank=True,
        related_name='thumbnail_image',
        on_delete=models.SET_NULL,
        help_text=gettext('The default thumbnail for articles, not to be '
                           'confused with \'Default cover image\'.'),
    )
    press_image_override = SVGImageField(
        upload_to=cover_images_upload_path,
        null=True,
        blank=True,
        storage=fs,
        help_text=gettext('Replaces the press logo in the footer.'),
    )
    default_cover_image = SVGImageField(
        upload_to=cover_images_upload_path,
        null=True,
        blank=True,
        storage=fs,
        help_text=gettext('The default cover image for journal issues and for '
                           'the journal\'s listing on the press-level website.'),
    )
    default_large_image = SVGImageField(
        upload_to=cover_images_upload_path,
        null=True,
        blank=True,
        storage=fs,
        help_text=gettext('The default background image for article openers '
                           'and carousel items.'),
    )
    header_image = SVGImageField(
        upload_to=cover_images_upload_path,
        null=True,
        blank=True,
        storage=fs,
        help_text=gettext('The logo-sized image at the top of all pages, '
                           'typically used for journal logos.'),
    )
    favicon = models.ImageField(
        upload_to=cover_images_upload_path,
        null=True,
        blank=True,
        storage=fs,
        help_text=gettext('The tiny round or square image appearing in browser '
                           'tabs before the webpage title'),
    )
    default_profile_image = SVGImageField(
        upload_to=cover_images_upload_path,
        null=True,
        blank=True,
        storage=fs,
        help_text=gettext('A default image displayed on the profile and '
                          'editorial team pages when the user has no set '
                          'profile image.'),
    )
    # DEPRECATED "description" in favour of "journal_description" setting
    description = JanewayBleachField(null=True, blank=True, verbose_name="Journal Description")
    contact_info = JanewayBleachField(null=True, blank=True, verbose_name="Contact Information")
    keywords = models.ManyToManyField(
        "submission.Keyword",
        blank=True,
        null=True,
        verbose_name="Discipline",
    )

    disable_metrics_display = models.BooleanField(default=False)
    disable_article_images = models.BooleanField(
        default=False,
        help_text=gettext('This field has been deprecated in v1.4.3'),
    )
    enable_correspondence_authors = models.BooleanField(default=True)
    disable_html_downloads = models.BooleanField(
        default=False,
        help_text='Used to disable download links for HTML files on the Article page.',
    )
    full_width_navbar = models.BooleanField(default=False)
    is_remote = models.BooleanField(
        default=False,
        help_text=gettext('When enabled, the journal is marked as not hosted in Janeway.'),
    )
    is_conference = models.BooleanField(default=False)
    is_archived = models.BooleanField(
        default=False,
        help_text="The journal is no longer publishing. This is only used as "
            "part of the journal metadata.",
    )
    remote_submit_url = models.URLField(
        blank=True,
        null=True,
        help_text=gettext('If the journal is remote you can link to its submission page.'),
    )
    remote_view_url = models.URLField(
        blank=True,
        null=True,
        help_text=gettext('If the journal is remote you can link to its home page.'),
    )
    view_pdf_button = models.BooleanField(
        default=False,
        help_text=gettext('Enables a "View PDF" link on article pages.'),
    )

    # Nav Items
    nav_home = models.BooleanField(default=True)
    nav_news = models.BooleanField(default=False)
    nav_articles = models.BooleanField(default=True)
    nav_issues = models.BooleanField(default=True)
    nav_collections = models.BooleanField(default=False)
    nav_contact = models.BooleanField(default=True)
    nav_start = models.BooleanField(default=True)
    nav_review = models.BooleanField(default=True)
    nav_sub = models.BooleanField(default=True)

    # (DEPRECATED)Boolean to determine if this journal has an XSLT file
    has_xslt = models.BooleanField(default=False)
    xsl = models.ForeignKey('core.XSLFile',
        default=default_xsl,
        on_delete=models.SET_DEFAULT,
        related_name="default_xsl",
    )

    # Boolean to determine if this journal should be hidden from the press
    hide_from_press = models.BooleanField(default=False)

    # Display sequence on the Journals page
    sequence = models.PositiveIntegerField(default=0)

    # this has to be handled this way so that we can add migrations to press
    try:
        press_name = press_models.Press.get_press(None).name
    except Exception:
        press_name = ''

    # Issue Display
    display_issue_volume = models.BooleanField(default=True)
    display_issue_number = models.BooleanField(default=True)
    display_issue_year = models.BooleanField(default=True)
    display_issue_title = models.BooleanField(default=True)
    display_article_number = models.BooleanField(
        default=False,
        help_text=gettext(
            "Whether to display article numbers. Article numbers are distinct " \
            "from article ID and can be set in Edit Metadata.",
        )
    )
    display_article_page_numbers = models.BooleanField(default=True)
    display_issue_doi = models.BooleanField(default=True)
    display_issues_grouped_by_decade = models.BooleanField(
        default=False,
        help_text='When enabled the issue page will group and display issues '
                  'by decade.',
    )

    disable_front_end = models.BooleanField(default=False)

    def __str__(self):
        if self.domain:
            return u'{0}: {1}'.format(self.code, self.domain)
        else:
            return self.code

    @staticmethod
    def override_cover(request, absolute=True):
        if request.journal.press_image_override:
            if absolute:
                return os.path.join(settings.BASE_DIR, 'files', 'journals', str(request.journal.pk),
                                    str(request.journal.press_image_override.uuid_filename))
            else:
                return os.path.join('files', 'journals', str(request.journal.pk),
                                    str(request.journal.press_image_override.uuid_filename))
        else:
            return None

    def get_setting(self, group_name, setting_name):
        return setting_handler.get_setting(group_name, setting_name, self, create=False).processed_value

    @property
    @cache(15)
    def name(self):
        try:
            return setting_handler.get_setting('general', 'journal_name', self, default=True).value
        except IndexError:
            self.name = 'Janeway Journal'
            return self.name

    @name.setter
    def name(self, value):
        setting_handler.save_setting('general', 'journal_name', self, value)

    @property
    def publisher(self):
        return setting_handler.get_setting('general', 'publisher_name', self, default=True).value

    @publisher.setter
    def publisher(self, value):
        setting_handler.save_setting('general', 'publisher_name', self, value)

    @property
    @cache(120)
    def issn(self):
        return setting_handler.get_setting('general', 'journal_issn', self, default=True).value

    @mutable_cached_property
    def doi(self):
        return setting_handler.get_setting('Identifiers', 'title_doi', self, default=True).value or None

    @doi.setter
    def doi_setter(self, value):
        setting_handler.save_setting('Identifiers', 'title_doi', self, value)

    @property
    @cache(120)
    def print_issn(self):
        return setting_handler.get_setting('general', 'print_issn', self, default=True).value

    @property
    @cache(120)
    def use_crossref(self):
        return setting_handler.get_setting('Identifiers', 'use_crossref', self, default=True).processed_value

    @issn.setter
    def issn(self, value):
        setting_handler.save_setting('general', 'journal_issn', self, value)

    @print_issn.setter
    def print_issn(self, value):
        setting_handler.save_setting('general', 'print_issn', self, value)

    @property
    def slack_logging_enabled(self):
        slack_webhook = setting_handler.get_setting('general', 'slack_webhook', self).value
        slack_logging = setting_handler.get_setting('general', 'slack_logging', self).processed_value

        if slack_logging and slack_webhook:
            return True
        else:
            return False

    @property
    def press(self):
        press = press_models.Press.objects.all().first()
        return press

    @classmethod
    def get_by_request(cls, request):
        obj, path = super().get_by_request(request)
        if not obj:
            # Lookup by code
            try:
                code = request.path.split('/')[1]
                obj = cls.objects.get(code=code)
                path = code
            except (IndexError, cls.DoesNotExist):
                pass
        return obj, path

    def site_url(self, path=""):
        if self.domain and not settings.URL_CONFIG == 'path':

            # Handle domain journal being browsed in path mode
            site_path = f'/{self.code}'
            if path and path.startswith(site_path):
                path = path[len(site_path):]
            return logic.build_url(
                    netloc=self.domain,
                    scheme=self._get_scheme(),
                    port=None,
                    path=path,
            )
        else:
            return self.press.site_path_url(self, path)

    def next_issue_order(self):
        issue_orders = [issue.order for issue in Issue.objects.filter(journal=self)]
        return max(issue_orders) + 1 if issue_orders else 0

    @property
    def issues(self):
        return Issue.objects.filter(journal=self)

    @property
    def issue_type_plural_name(self):
        try:
            issue_type = IssueType.objects.get(journal=self, code="issue")
            return issue_type.plural_name
        except IssueType.DoesNotExist:
            return None

    def serial_issues(self):
        return Issue.objects.filter(journal=self, issue_type__code='issue')

    @property
    def published_issues(self):
        return Issue.objects.filter(
            journal=self,
            date__lte=timezone.now(),
        )

    def issues_by_decade(self, issues_to_sort=None):
        issue_decade_dict = {}

        if not issues_to_sort:
            issues_to_sort = Issue.objects.filter(
                journal=self,
                date__lte=timezone.now(),
                issue_type__code='issue',
            )
        for issue in issues_to_sort:
            issue_year = issue.date_published.year
            decade_start = issue_year - (issue_year % 10)
            decade_end = decade_start + 9

            # if the decade is greater than the current year, cap at the
            # current year.
            date = timezone.now().date()
            if decade_end > date.year:
                decade_end = date.year

            decade_span = f"{decade_start} - {decade_end}"
            if issue_decade_dict.get(decade_span):
                issue_decade_dict[decade_span].append(issue)
            else:
                issue_decade_dict[decade_span] = [issue]
        return issue_decade_dict

    def editors(self):
        """ Returns all users enrolled as editors for the journal
        :return: A queryset of core.models.Account
        """
        return core_models.Account.objects.filter(
                accountrole__role__slug="editor",
                accountrole__journal=self,
        )

    def users_with_role(self, role):
        pks = [
            role.user.pk for role in core_models.AccountRole.objects.filter(
                role__slug=role,
                journal=self,
            ).prefetch_related('user')
        ]
        return core_models.Account.objects.filter(pk__in=pks)

    def users_with_role_count(self, role):
        return core_models.AccountRole.objects.filter(
            role__slug=role,
            journal=self,
        ).count()

    def editor_pks(self):
        return [[str(role.user.pk), str(role.user.pk)] for role in
                core_models.AccountRole.objects.filter(role__slug='editor', journal=self)]

    def journal_users(self, objects=True):
        account_roles = core_models.AccountRole.objects.filter(
            journal=self,
            user__is_active=True,
        ).select_related('user')

        if objects:
            users = {role.user for role in account_roles}
        else:
            users = {role.user.pk for role in account_roles}

        return users

    @cache(300)
    def editorial_groups(self):
        return core_models.EditorialGroup.objects.filter(journal=self)

    @property
    def editor_emails(self):
        editor_roles = core_models.AccountRole.objects.filter(role__slug='editor', journal=self)
        return [role.user.email for role in editor_roles]

    def next_featured_article_order(self):
        orderings = [featured_article.sequence for featured_article in self.featuredarticle_set.all()]
        return max(orderings) + 1 if orderings else 0

    def next_contact_order(self):
        contacts = core_models.Contacts.objects.filter(content_type__model='journal', object_id=self.pk)
        orderings = [contact.sequence for contact in contacts]
        return max(orderings) + 1 if orderings else 0

    def next_group_order(self):
        orderings = [group.sequence for group in self.editorialgroup_set.all()]
        return max(orderings) + 1 if orderings else 0

    @property
    def scss_files(self):
        import journal.logic as journal_logic
        return journal_logic.list_scss(self)

    @property
    def active_carousel(self):
        """ Renders a carousel for the journal homepage.
        :return: a tuple containing the active carousel and list of associated articles
        """
        if self.carousel is None or not self.carousel.enabled:
            return None, []
        items = self.carousel.get_items()
        if self.carousel.current_issue and self.current_issue:
            items = chain([self.current_issue], items)

        return self.carousel, items

    def next_pa_seq(self):
        "Works out what the next pinned article sequence should be."
        pinned_articles = PinnedArticle.objects.filter(journal=self).reverse()
        if pinned_articles:
            return pinned_articles[0].sequence + 1
        else:
            return 0

    def setup_directory(self):
        directory = os.path.join(settings.BASE_DIR, 'files', 'journals', str(self.pk))
        if not os.path.exists(directory):
            os.makedirs(directory)

    def workflow(self):
        try:
            return core_models.Workflow.objects.get(journal=self)
        except core_models.Workflow.DoesNotExist:
            return workflow.create_default_workflow(self)

    def element_in_workflow(self, element_name):
        try:
            element = core_models.WorkflowElement.objects.get(element_name=element_name, journal=self)
            if element in self.workflow().elements.all():
                return True
            else:
                return False
        except core_models.WorkflowElement.DoesNotExist:
            return False

    @property
    def published_articles(self):
        return submission_models.Article.objects.filter(
            journal=self,
            stage=submission_models.STAGE_PUBLISHED,
            date_published__lte=timezone.now(),
        )

    def article_keywords(self):
        return submission_models.Keyword.objects.filter(
            article__in=self.published_articles
        ).order_by('word').distinct()

    @property
    def workflow_plugin_elements(self):
        return self.workflowelement_set.exclude(
            element_name__in=workflow.core_workflow_element_names()
        )

    @property
    def description_for_press(self):
        press_description = self.get_setting(
            group_name='general',
            setting_name='press_journal_description'
        )
        if press_description:
            return press_description
        else:
            return self.get_setting(
                group_name='general',
                setting_name='journal_description',
            )

    def setup_default_review_form(self):
        default_review_form, c = review_models.ReviewForm.objects.get_or_create(
            journal=self,
            name='Default Form',
            defaults={
                'intro': 'Please complete the form below.',
                'thanks': 'Thank you for completing the review.',
            }
        )

        if c:
            main_element = review_models.ReviewFormElement.objects.create(
                name='Review',
                kind='textarea',
                required=True,
                order=1,
                width='large-12 columns',
                help_text=gettext('Please add as much detail as you can.'),
            )

            default_review_form.elements.add(main_element)


class PinnedArticle(models.Model):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
    )
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    sequence = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('sequence',)

    def __str__(self):
        return '{0}, {1}: {2}'.format(self.sequence, self.journal.code, self.article.title)


ISSUE_CODE_RE = re.compile("^[a-zA-Z0-9-_]+$")


class IssueQuerySet(models.QuerySet):

    def open_for_submission(self):
        """Build a queryset of Issues open for submission."""
        _now = timezone.now()
        return self.filter(
            models.Q(date_close__isnull=True) | models.Q(date_close__gte=_now),
            models.Q(date_open__isnull=True) | models.Q(date_open__lte=_now)
        )

    def current_journal(self, journal):
        """Build a queryset of Issues for the current journal."""
        return self.filter(journal=journal)

    def by_user(self, user):
        """Build a queryset of Issues available to the current user.

        This means user is included in Issue.invitees for any issue or  without invitees or with the user in the invitees.
        """
        if user and user.is_authenticated:
            return self.filter(
                models.Q(invitees__isnull=True) | models.Q(invitees__in=[user]),
            )
        else:
            return self.none()


class Issue(AbstractLastModifiedModel):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
    )

    # issue metadata
    volume = models.IntegerField(default=1)
    issue = models.CharField(max_length=255, default="1")
    short_name = models.CharField(blank=True, max_length=300, help_text=gettext("Internal issue name"), default="")
    issue_title = models.CharField(blank=True, max_length=300)
    cached_display_title = models.CharField(
        null=True, blank=True, max_length=300,
        editable=False,
        help_text=gettext(
            "Autogenerated cache of the display format of an issue title"
        ),
    )
    date = models.DateTimeField(default=timezone.now)
    order = models.IntegerField(default=0)
    issue_type = models.ForeignKey(
        "journal.IssueType", blank=False, null=True, on_delete=models.SET_NULL)
    # To be deprecated in 1.3.7
    old_issue_type = models.CharField(max_length=200, default='Issue', choices=ISSUE_TYPES, null=True, blank=True)
    issue_description = JanewayBleachField(blank=True, null=True)
    short_description = models.CharField(max_length=600, blank=True, null=True)

    cover_image = SVGImageField(
        upload_to=cover_images_upload_path, null=True, blank=True, storage=fs,
        help_text=gettext(
            "Image representing the cover of a printed issue or volume",
        )
    )
    large_image = SVGImageField(
        upload_to=issue_large_image_path, null=True, blank=True, storage=fs,
        help_text=gettext(
            "landscape hero image used in the carousel and issue page"
        )
    )

    # issue articles
    articles = models.ManyToManyField('submission.Article', blank=True, null=True, related_name='issues')

    # guest editors
    editors = models.ManyToManyField(
        'core.Account',
        blank=True,
        null=True,
        related_name='guest_editors',
        through='IssueEditor',
    )

    code = models.SlugField(
        max_length=700, null=True, blank=True,
        help_text=gettext(
            "An optional alphanumeric code (Slug) used to generate a verbose "
            " url for this issue. e.g: 'winter-special-issue'."
        ),
    )

    doi = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='DOI',
        help_text='The DOI (not URL) to be registered for the issue when registering '
                  'articles that are part of this issue. If you have enabled issue '
                  'autoregistration in your settings, this field should not be '
                  'entered manually.',
        )

    isbn = models.CharField(
        max_length=28,
        blank=True,
        null=True,
        verbose_name="ISBN",
        help_text=gettext(
            "An ISBN is relevant for non-serial collections such as"
            " conference proceedings"
        ),
    )
    description = JanewayBleachField(
        verbose_name=gettext("Issue presentation"),
        help_text=gettext("Rich text description of the issue for the issue page."),
        default="", blank=True
    )
    date_open = models.DateTimeField(null=True, blank=True, verbose_name=gettext("Date of submission opening"))
    date_close = models.DateTimeField(null=True, blank=True, verbose_name=gettext("Date of submission closing"))
    invitees = models.ManyToManyField(
        "core.Account",
        blank=True,
        related_name="invited_issues",
    )
    allowed_sections = models.ManyToManyField(
        "submission.Section",
        blank=True,
    )
    managing_editors = models.ManyToManyField(
        "core.Account",
        blank=True,
        related_name="managed_issue",
    )
    documents = models.ManyToManyField(
        "core.File",
        blank=True,
        related_name="issue_documents",
    )
    expected_submissions = models.IntegerField(null=True, blank=True, help_text=gettext("Expected number of submissions"))
    internal_notes = models.TextField(blank=True, null=True)

    objects = IssueQuerySet.as_manager()

    @cached_property
    def doi_url(self):
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return ''

    @property
    def hero_image_url(self):
        if self.large_image:
            return self.large_image.url
        elif self.journal.default_large_image:
            return self.journal.default_large_image.url
        else:
            return ''

    @property
    def date_published(self):
        return datetime.datetime(
            self.date.year, self.date.month, self.date.day,
            tzinfo=self.date.tzinfo,
        )

    @property
    def url(self):
        if self.is_serial:
            path = reverse("journal_issue", kwargs={"issue_id": self.pk})
        else:
            path = reverse(
                "journal_collection", kwargs={"collection_id": self.pk})
        return self.journal.site_url(path=path)

    @property
    def carousel_subtitle(self):
        if not self.is_serial:
            return self.issue_type.pretty_name
        if self == self.journal.current_issue:
            return gettext("Current Issue")
        else:
            return ""

    @property
    def carousel_title(self):
        return self.display_title

    @property
    def carousel_image_resolver(self):
        return 'news_file_download'

    @property
    def is_serial(self):
        if self.issue_type.code == 'issue':
            return True
        else:
            return False

    @cached_property
    def display_title(self):
        return mark_safe(
            self.cached_display_title
            or self.update_display_title(save=True)
        )

    def update_display_title(self, save=False):
        title = None
        if self.issue_type and self.issue_type.code == 'issue':
            if save:
                self.save()
                return self.cached_display_title
            title = self.cached_display_title = self.pretty_issue_identifier
        else:
            self.cached_display_title = ''
            title = self.issue_title

        return title

    def issue_title_parts(self, article=None):
        journal = self.journal
        volume = issue = year = issue_title = article_number = page_numbers = ''

        if journal.display_issue_volume and self.volume:
            volume = "{%% trans 'Volume' %%} %s" % self.volume
        if journal.display_issue_number and self.issue and self.issue != "0":
            issue = "{%% trans 'Issue' %%} %s" % self.issue
        if journal.display_issue_year and self.date:
            year = "{}".format(self.date.year)
        if journal.display_issue_title:
            issue_title = self.issue_title
        if journal.display_article_number and article and article.article_number:
            article_number = "{%% trans 'Article' %%} %s" % article.article_number
        if journal.display_article_page_numbers and article:
            if article.page_range:
                page_numbers = article.page_range
            elif article.total_pages:
                if article.total_pages != 1:
                    label = gettext('pages')
                else:
                    label = gettext('page')
                num_pages = str(article.total_pages)
                page_numbers = f"{num_pages} {label}"

        return [volume, issue, year, issue_title, article_number, page_numbers]

    @property
    def pretty_issue_identifier(self):
        template = Template(
            " &bull; ".join((filter(None, self.issue_title_parts()))),
        )
        return mark_safe(template.render(Context()))

    @property
    def non_pretty_issue_identifier(self):
        return Template(
            " ".join((filter(None, self.issue_title_parts())))
        ).render(Context())

    @property
    def manage_issue_list(self):
        section_article_dict = collections.OrderedDict()

        article_pks = [article.pk for article in self.articles.all()]

        # Find explicitly ordered sections for this issue
        ordered_sections = SectionOrdering.objects.filter(issue=self)

        for ordered_section in ordered_sections:
            article_list = list()

            ordered_articles = ArticleOrdering.objects.filter(issue=self, section=ordered_section.section)

            for article in ordered_articles:
                article_list.append(article.article)

            articles = self.articles.filter(section=ordered_section.section, pk__in=article_pks)

            for article in articles:
                if not article in article_list:
                    article_list.append(article)

            section_article_dict[ordered_section.section] = article_list

        # Handle all other sections that have articles in this issue.
        for article in self.articles.all():
            if not section_article_dict.get(article.section):
                article_list = list()
                articles = self.articles.filter(section=article.section, pk__in=article_pks).order_by('section')

                for article in articles:
                    article_list.append(article)

                section_article_dict[article.section] = article_list

        return section_article_dict

    @property
    def all_sections(self):
        ordered_sections = [order.section for order in SectionOrdering.objects.filter(issue=self)]
        articles = self.articles.all().order_by('section')

        for article in articles:
            if not article.section in ordered_sections:
                ordered_sections.append(article.section)

        return ordered_sections

    @property
    def first_section(self):
        all_sections = self.all_sections

        if all_sections:
            return all_sections[0]
        else:
            return 0

    @property
    def last_section(self):
        all_sections = self.all_sections

        if all_sections:
            return all_sections[-1]
        else:
            return 0

    @property
    def issue_articles(self):
        # this property should be used to display article ToCs since
        # it enforces visibility of Published items
        articles = self.articles.filter(
            stage=submission_models.STAGE_PUBLISHED,
            date_published__lte=timezone.now(),
        )

        ordered_list = list()
        for article in articles:
            ordered_list.append({'article': article, 'order': self.get_article_order(article)})

        return sorted(ordered_list, key=itemgetter('order'))

    def structure(self):
        # This method is very inefficient and is not used in core anymore
        # Kept for backwards compatibility with 3rd party themes
        logger.warning(
            "Using 'Issue.structure' will be deprecated as of Janeway 1.4"
        )
        structure = collections.OrderedDict()

        sections = self.all_sections
        articles = self.articles.filter(
            stage=submission_models.STAGE_PUBLISHED,
            date_published__lte=timezone.now(),
        )

        for section in sections:
            article_with_order = ArticleOrdering.objects.filter(
                issue=self,
                section=section,
                article__stage=submission_models.STAGE_PUBLISHED,
                article__date_published__lte=timezone.now(),
            )

            article_list = list()
            for order in article_with_order:
                article_list.append(order.article)

            for article in articles.filter(section=section):
                if not article in article_list:
                    article_list.append(article)
            structure[section] = article_list

        return structure

    def get_sorted_articles(self, published_only=True):
        """ Returns issue articles sorted by section and article order

        Many fields are prefetched and annotated to handle large issues more
        eficiently. In particular, it annotates relevant SectionOrder and
        ArticleOrdering rows as section_order and article_order respectively.
        Returns a Queryset which should keep the memory footprint at a minimum
        """

        section_order_subquery = SectionOrdering.objects.filter(
            section=OuterRef("section__pk"),
            issue=Value(self.pk),
        ).values_list("order")

        article_order_subquery = ArticleOrdering.objects.filter(
            section=OuterRef("section__pk"),
            article=OuterRef("pk"),
            issue=Value(self.pk),
        ).values_list("order")

        issue_articles = self.articles.prefetch_related(
            'authors',
            'frozenauthor_set',
            'manuscript_files',
        ).select_related(
            'section',
        ).annotate(
            section_order=Subquery(section_order_subquery),
            article_order=Subquery(article_order_subquery),
        ).order_by(
            "section_order",
            "section__sequence",
            "section__pk",
            "article_order",
        )

        if published_only:
            issue_articles = issue_articles.filter(
                stage=submission_models.STAGE_PUBLISHED,
                date_published__lte=timezone.now(),
            )

        return issue_articles

    @property
    def article_pks(self):
        return [article.pk for article in self.articles.all()]

    def get_article_order(self, article):
        try:
            try:
                ordering = ArticleOrdering.objects.get(article=article, issue=self)
                return ordering.order
            except ArticleOrdering.MultipleObjectsReturned:
                orderings = ArticleOrdering.objects.filter(article=article, issue=self)
                return orderings[0]
        except ArticleOrdering.DoesNotExist:
            return 0

    def next_order(self):
        orderings = [ordering.order for ordering in ArticleOrdering.objects.filter(issue=self)]
        return max(orderings) + 1 if orderings else 0

    @staticmethod
    def auto_increment_volume_issue(journal):
        """
        Takes a journal as input
        Looks at latest non-collection issue in journal,
        Returns a tuple of ints representing the next (volume, issue)
        """
        from datetime import datetime

        # get the latest issue from the specified journal
        try:
            latest_issue = Issue.objects.filter(
                journal=journal,
                issue_type__code='issue',
            ).latest('date')

        # if no issues in journal, start at 1:1
        except Issue.DoesNotExist:
            return (1, "1")

        # if issues exist, iterate - if new year, add 1 to volume and reset issue to 1
        # otherwise keep volume the same and add 1 to issue
        else:
            if datetime.now().year > latest_issue.date.year:
                volume = latest_issue.volume + 1
                issue = "1"
                return (volume, issue)
            else:
                if latest_issue.issue.isdigit():
                    issue = int(latest_issue.issue) + 1
                    return (latest_issue.volume, str(issue))
                else:
                    raise TypeError(
                        "Can't auto increase issue number after issue %s",
                        latest_issue.issue,
                    )

    def is_published(self):
        if self.date and self.date < timezone.now():
            return True
        return False

    def order_articles_in_sections(self, sort_field, order):
        order_by_string = '{}{}'.format(
            '-' if order == 'dsc' else '',
            sort_field,
        )

        for section in self.all_sections:
            section_articles = self.articles.filter(
                section=section
            ).order_by(
                order_by_string,
            )
            ids_in_order = [section_article.pk for section_article in section_articles]
            for article in section_articles:
                article_ordering, _ = ArticleOrdering.objects.get_or_create(
                    issue=self,
                    section=section,
                    article=article,
                )
                article_ordering.order = ids_in_order.index(article_ordering.article.pk)
                article_ordering.save()

    def save(self, *args, **kwargs):
        # get the currently enabled languages for this journal or the default
        journal_languages = self.journal.get_setting(
            'general',
            'journal_languages',
        ) or [settings.LANGUAGE_CODE]

        for lang in journal_languages:
            with translation.override(lang):
                # set save as False to avoid infinite recursion
                self.update_display_title(save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            '{self.issue_type.pretty_name}: '
            '{self.issue}({self.volume}) '
            '{self.issue_title} ({self.date.year})'.format(self=self)
        )

    class Meta:
        ordering = ("order", "-date")
        unique_together = ("journal", "code")


class IssueType(models.Model):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
    )
    code = models.CharField(max_length=255)

    pretty_name = models.CharField(max_length=255)
    custom_plural = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return (
            self.custom_plural
            or self.pretty_name
            or "{self.code}".format(self=self)
        )


    @property
    def plural_name(self):
        return self.custom_plural or "{self.pretty_name}s".format(self=self)

    class Meta:
        unique_together = ('journal', 'code')


class IssueGalley(models.Model):
    FILES_PATH = 'issues'

    file = models.ForeignKey(
        'core.File',
        on_delete=models.CASCADE,
    )
    # An Issue can only have one galley at this time (PDF)
    issue = models.OneToOneField(
        'journal.Issue',
        related_name='galley',
        on_delete=models.CASCADE,
    )

    @transaction.atomic
    def replace_file(self, other):
        new_file = files.overwrite_file(other, self.file, self.path_parts)
        self.file = new_file
        self.save()

    def serve(self, request):
        public = True
        return files.serve_any_file(
            request,
            self.file,
            public,
            path_parts=self.path_parts,
        )

    @property
    def path_parts(self):
        path_parts = (self.FILES_PATH, self.issue.pk)
        return path_parts


class IssueEditor(models.Model):
    account = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
    )
    role = models.CharField(
        max_length=255,
        default='Guest Editor',
    )
    sequence = models.PositiveIntegerField(
        default=1,
        help_text='Provides for ordering of the Issue Editors.'
    )

    class Meta:
        ordering = ('sequence', 'account')

    def __str__(self):
        return "{user} {role}".format(
            user=self.account.full_name(),
            role=self.role,
        )


class SectionOrdering(models.Model):
    section = models.ForeignKey(
        'submission.Section',
        on_delete=models.CASCADE,
    )
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return "{0}: {1}, ({2} {3}) {4}".format(self.order, self.issue.issue_title, self.issue.volume, self.issue.issue, self.section)

    class Meta:
        ordering = ('order', 'section')


class ArticleOrdering(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
    )
    section = models.ForeignKey(
        'submission.Section',
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('article', 'issue', 'section')
        ordering = ('order', 'section')

    def __str__(self):
        return "{0}: {1}, {2}".format(self.order, self.section, self.article.title)


class FixedPubCheckItems(models.Model):
    article = models.OneToOneField(
        'submission.Article',
        on_delete=models.CASCADE,
    )

    metadata = models.BooleanField(default=False)
    verify_doi = models.BooleanField(default=False)
    select_issue = models.BooleanField(default=False)
    set_pub_date = models.BooleanField(default=False)
    send_notifications = models.BooleanField(default=False)
    select_render_galley = models.BooleanField(default=False)
    select_article_image = models.BooleanField(default=False)
    select_open_reviews = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Fixed pub check items'


class PresetPublicationCheckItem(models.Model):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
    )

    title = models.TextField()
    text = JanewayBleachField()
    enabled = models.BooleanField(default=True)


class PrePublicationChecklistItem(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )

    completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        'core.Account',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    completed_on = models.DateTimeField(blank=True, null=True)

    title = models.TextField()
    text = JanewayBleachField()

    def __str__(self):
        return "{0} - {1}".format(self.pk, self.title)


class BannedIPs(models.Model):
    ip = models.GenericIPAddressField()
    date_banned = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Banned IPs"


def notification_type():
    return (
        ('submission', 'Submission'),
        ('acceptance', 'Acceptance'),
    )


class Notifications(models.Model):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    domain = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=notification_type())
    active = models.BooleanField(default=False)

    def __str__(self):
        return '{0}, {1}: {2}'.format(self.journal, self.user, self.domain)

    class Meta:
        verbose_name_plural = 'notifications'


# Signals

@receiver(post_save, sender=Journal)
def setup_default_section(sender, instance, created, **kwargs):
    if created:
        with translation.override(settings.LANGUAGE_CODE):
            submission_models.Section.objects.get_or_create(
                journal=instance,
                number_of_reviewers=2,
                name='Article',
                plural='Articles'
            )


@receiver(post_save, sender=Journal)
def setup_default_workflow(sender, instance, created, **kwargs):
    if created:
        workflow.create_default_workflow(instance)


@receiver(post_save, sender=Journal)
def setup_submission_configuration(sender, instance, created, **kwargs):
    if created:
        submission_models.SubmissionConfiguration.objects.get_or_create(
            journal=instance,
        )


@receiver(post_save, sender=Journal)
def setup_licenses(sender, instance, created, **kwargs):
    if created:
        install.update_license(
            instance,
        )


@receiver(post_save, sender=Journal)
def setup_submission_items(sender, instance, created, **kwargs):
    if created:
        install.setup_submission_items(
            instance,
        )


@receiver(post_save, sender=Journal)
def setup_default_form(sender, instance, created, **kwargs):
    # if this is a new journal and there is not default review for already
    # create a new one with a default review element.
    if created and not review_models.ReviewForm.objects.filter(
            journal=instance,
    ).exists():
        instance.setup_default_review_form()



@receiver(post_save, sender=Journal)
def update_issue_display_title(sender, instance, created, **kwargs):
    for issue in Issue.objects.filter(journal=instance):
        issue.save()


@receiver(post_save, sender=Journal)
def setup_journal_file_directory(sender, instance, created, **kwargs):
    if created:
        instance.setup_directory()


def issue_articles_change(sender, **kwargs):
    """
    When an article is removed from an issue this signal will delete any
    orderings for that article in the issue.
    """
    supported_actions = ['post_remove', 'post_add']
    issue_or_article = kwargs.get('instance')
    action = kwargs.get('action')
    update_side = kwargs.get('reverse')

    if issue_or_article and action in supported_actions:
        object_pks = kwargs.get('pk_set', [])
        for object_pk in object_pks:

            if update_side:
                article = issue_or_article
                issue = Issue.objects.get(pk=object_pk)
            else:
                article = submission_models.Article.objects.get(pk=object_pk)
                issue = issue_or_article

            if action == 'post_remove':
                try:
                    ordering = ArticleOrdering.objects.get(
                        issue=issue,
                        article=article,
                    ).delete()
                except ArticleOrdering.DoesNotExist:
                    pass

                # if this is the last Article of this Section, remove SectionOrdering for that Section.
                try:
                    if not issue.articles.filter(
                        section=article.section,
                    ).exists():
                        section_ordering = SectionOrdering.objects.get(
                            issue=issue,
                            section=article.section,
                        ).delete()
                except SectionOrdering.DoesNotExist:
                    pass

                if issue == article.primary_issue:
                    if article.issues_list().exists():
                        article.primary_issue = article.issues_list().first()
                    else:
                        article.primary_issue = None
                    article.save()

            elif action == 'post_add':
                ArticleOrdering.objects.get_or_create(
                    issue=issue,
                    article=article,
                    section=article.section,
                    order=issue.next_order(),
                )

                if not article.primary_issue:
                    article.primary_issue = issue
                    article.save()


m2m_changed.connect(issue_articles_change, sender=Issue.articles.through)

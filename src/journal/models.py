__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from operator import itemgetter
import collections
import uuid
import os

from django.conf import settings
from django.db import models, transaction
from django.db.models import OuterRef, Subquery, Value
from django.db.models.signals import post_save, m2m_changed
from django.utils.safestring import mark_safe
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from core import (
        files,
        models as core_models,
        workflow,
)
from core.file_system import JanewayFileSystemStorage
from core.model_utils import AbstractSiteModel
from press import models as press_models
from submission import models as submission_models
from utils import setting_handler, logic
from utils.function_cache import cache
from utils.logger import get_logger

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
    code = models.CharField(max_length=15, unique=True)
    current_issue = models.ForeignKey('Issue', related_name='current_issue', null=True, blank=True,
                                      on_delete=models.SET_NULL)
    carousel = models.OneToOneField('carousel.Carousel', related_name='journal', null=True, blank=True)
    thumbnail_image = models.ForeignKey('core.File', null=True, blank=True, related_name='thumbnail_image',
                                        on_delete=models.SET_NULL)
    press_image_override = models.ForeignKey('core.File', null=True, blank=True, related_name='press_image_override')
    default_cover_image = models.ImageField(upload_to=cover_images_upload_path, null=True, blank=True, storage=fs)
    default_large_image = models.ImageField(upload_to=cover_images_upload_path, null=True, blank=True, storage=fs)
    header_image = models.ImageField(upload_to=cover_images_upload_path, null=True, blank=True, storage=fs)
    favicon = models.ImageField(upload_to=cover_images_upload_path, null=True, blank=True, storage=fs)
    description = models.TextField(null=True, blank=True, verbose_name="Journal Description")
    contact_info = models.TextField(null=True, blank=True, verbose_name="Contact Information")
    keywords = models.ManyToManyField("submission.Keyword", blank=True, null=True)

    disable_metrics_display = models.BooleanField(default=False)
    disable_article_images = models.BooleanField(default=False)
    enable_correspondence_authors = models.BooleanField(default=True)
    disable_html_downloads = models.BooleanField(default=False)
    full_width_navbar = models.BooleanField(default=False)
    is_remote = models.BooleanField(default=False)
    is_conference = models.BooleanField(default=False)
    remote_submit_url = models.URLField(blank=True, null=True)
    remote_view_url = models.URLField(blank=True, null=True)
    view_pdf_button = models.BooleanField(
        default=False,
        help_text='Enables a "View PDF" link on article pages.'
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
    except BaseException:
        press_name = ''

    # Issue Display
    display_issue_volume = models.BooleanField(default=True)
    display_issue_number = models.BooleanField(default=True)
    display_issue_year = models.BooleanField(default=True)
    display_issue_title = models.BooleanField(default=True)

    disable_front_end = models.BooleanField(default=False)

    def __str__(self):
        return u'{0}: {1}'.format(self.code, self.domain)

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
    @cache(300)
    def name(self):
        try:
            return setting_handler.get_setting('general', 'journal_name', self, create=False, fallback='en').value
        except IndexError:
            self.name = 'Janeway Journal'
            return self.name

    @name.setter
    def name(self, value):
        setting_handler.save_setting('general', 'journal_name', self, value)

    @property
    def publisher(self):
        return setting_handler.get_setting('general', 'publisher_name', self, create=False, fallback='en').value

    @publisher.setter
    def publisher(self, value):
        setting_handler.save_setting('general', 'publisher_name', self, value)

    @property
    @cache(120)
    def issn(self):
        return setting_handler.get_setting('general', 'journal_issn', self, create=False, fallback='en').value

    @property
    @cache(120)
    def use_crossref(self):
        try:
            return setting_handler.get_setting('Identifiers',
                                               'crossref_prefix',
                                               self,
                                               create=False,
                                               fallback='en').processed_value
        except IndexError:
            return False

    @issn.setter
    def issn(self, value):
        setting_handler.save_setting('general', 'journal_issn', self, value)

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
        press = press_models.Press.objects.all()[0]
        return press

    def site_url(self, path=""):
        if settings.URL_CONFIG == "path":
            return self._site_path_url(path)

        return logic.build_url(
                netloc=self.domain,
                scheme=self.SCHEMES[self.is_secure],
                port=None,
                path=path,
        )

    def _site_path_url(self, path=None):
        request = logic.get_current_request()
        if request and request.journal == self:
            if not path:
                path = "/{}".format(self.code)
            return request.build_absolute_uri(path)
        else:
            return self.press.journal_path_url(self, path)

    def full_url(self, request=None):
        logger.warning("Using journal.full_url is deprecated")
        return self.site_url()

    def full_reverse(self, request, url_name, kwargs):
        base_url = self.full_url(request)
        url_path = reverse(url_name, kwargs=kwargs)
        return "{0}{1}".format(base_url, url_path)

    def next_issue_order(self):
        issue_orders = [issue.order for issue in Issue.objects.filter(journal=self)]
        return max(issue_orders) + 1 if issue_orders else 0

    def issues(self):
        return Issue.objects.filter(journal=self)

    def editors(self):
        pks = [role.user.pk for role in core_models.AccountRole.objects.filter(role__slug='editor', journal=self)]
        return core_models.Account.objects.filter(pk__in=pks)

    def users_with_role(self, role):
        pks = [
            role.user.pk for role in core_models.AccountRole.objects.filter(
                role__slug=role,
                journal=self,
            ).prefetch_related('user')
        ]
        return core_models.Account.objects.filter(pk__in=pks)

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
        import core.logic as core_logic
        carousel_objects = []
        article_objects = []
        news_objects = []

        if self.carousel is None:
            return None, []

        if self.carousel.mode == 'off':
            return self.carousel, []

        # determine the carousel mode and build the list of objects as appropriate
        if self.carousel.mode == "latest":
            article_objects = core_logic.latest_articles(self.carousel, 'journal')

        elif self.carousel.mode == "selected":
            article_objects = core_logic.selected_articles(self.carousel, 'journal')

        elif self.carousel.mode == "news":
            news_objects = core_logic.news_items(self.carousel, 'journal')

        elif self.carousel.mode == "mixed":
            # news items and latest articles
            news_objects = core_logic.news_items(self.carousel, 'journal')
            article_objects = core_logic.latest_articles(self.carousel, 'journal')

        elif self.carousel.mode == "mixed-selected":
            # news items and latest articles
            news_objects = self.carousel.news_articles.all()
            article_objects = core_logic.selected_articles(self.carousel)

        # run the exclusion routine
        if self.carousel.mode != "news" and self.carousel.exclude:
            # remove articles from the list here when the user has specified that certain articles
            # should be excluded
            exclude_list = self.carousel.articles.all()
            excluded = exclude_list.values_list('id', flat=True)
            try:
                article_objects = article_objects.exclude(id__in=excluded)
            except AttributeError:
                for exclude_item in exclude_list:
                    if exclude_item in article_objects:
                        article_objects.remove(exclude_item)

        # now limit the items by the respective amounts
        if self.carousel.article_limit > 0:
            article_objects = article_objects[:self.carousel.article_limit]

        if self.carousel.news_limit > 0:
            news_objects = news_objects[:self.carousel.news_limit]

        # if running in a mixed mode, sort the objects by a mixture of date_published for articles and posted for
        # news items. Note, this has to be done AFTER the exclude procedure above.
        if self.carousel.mode == "mixed-selected" or self.carousel.mode == 'mixed':
            carousel_objects = core_logic.sort_mixed(article_objects, news_objects)
        elif self.carousel.mode == 'news':
            carousel_objects = news_objects
        else:
            carousel_objects = article_objects

        return self.carousel, carousel_objects

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
        ).order_by('word')

    @property
    def workflow_plugin_elements(self):
        return self.workflowelement_set.exclude(
            element_name__in=workflow.core_workflow_element_names()
        )


class PinnedArticle(models.Model):
    journal = models.ForeignKey(Journal)
    article = models.ForeignKey('submission.Article')
    sequence = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('sequence',)

    def __str__(self):
        return '{0}, {1}: {2}'.format(self.sequence, self.journal.code, self.article.title)


class Issue(models.Model):
    journal = models.ForeignKey(Journal)

    # issue metadata
    volume = models.IntegerField(default=1)
    issue = models.IntegerField(default=1)
    issue_title = models.CharField(blank=True, max_length=300)
    date = models.DateTimeField(default=timezone.now)
    order = models.IntegerField(default=0)
    issue_type = models.ForeignKey(
        "journal.IssueType", blank=False, null=True, on_delete=models.SET_NULL)
    # To be deprecated in 1.3.7
    old_issue_type = models.CharField(max_length=200, default='Issue', choices=ISSUE_TYPES, null=True, blank=True)
    issue_description = models.TextField(blank=True, null=True)

    cover_image = models.ImageField(upload_to=cover_images_upload_path, null=True, blank=True, storage=fs)
    large_image = models.ImageField(upload_to=issue_large_image_path, null=True, blank=True, storage=fs)

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

    class Meta:
        ordering = ('order', 'year', 'volume', 'issue', 'title')

    @property
    def display_title(self):
        if self.issue_type.code != 'issue':
            return self.issue_title

        journal = self.journal
        issue_identifier = self.pretty_issue_identifier

        title = "{}".format(
            self.issue_title) if journal.display_issue_title else ""

        title_list = [issue_identifier, title]

        return mark_safe(" &bull; ".join((filter(None, title_list))))

    @property
    def pretty_issue_identifier(self):
        journal = self.journal

        volume = "Volume {}".format(
            self.volume) if journal.display_issue_volume else ""
        issue = "Issue {}".format(
            self.issue) if journal.display_issue_number else ""
        year = "{}".format(
            self.date.year) if journal.display_issue_year else ""

        parts = [volume, issue, year]

        return mark_safe(" &bull; ".join((filter(None, parts))))


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
                article_list.append(article)

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
            latest_issue = Issue.objects.filter(journal=journal, issue_type='Issue').latest('date')

        # if no issues in journal, start at 1:1
        except Issue.DoesNotExist:
            return (1, 1)

        # if issues exist, iterate - if new year, add 1 to volume and reset issue to 1
        # otherwise keep volume the same and add 1 to issue
        else:
            if datetime.now().year > latest_issue.date.year:
                volume = latest_issue.volume + 1
                issue = 1
                return (volume, issue)
            else:
                issue = latest_issue.issue + 1
                return (latest_issue.volume, issue)

    def __str__(self):
        return u'{0}: {1} {2} ({3})'.format(self.volume, self.issue, self.issue_title, self.date.year)

    class Meta:
        ordering = ("order", "-date")


class IssueType(models.Model):
    journal = models.ForeignKey(Journal)
    code = models.CharField(max_length=255)

    pretty_name = models.CharField(max_length=255)
    custom_plural = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "{self.code}".format(self=self)

    @property
    def plural_name(self):
        return self.custom_plural or "{self.pretty_name}s".format(self=self)

    class Meta:
        unique_together = ('journal', 'code')


class IssueGalley(models.Model):
    FILES_PATH = 'issues'

    file = models.ForeignKey('core.File')
    # An Issue can only have one galley at this time (PDF)
    issue = models.OneToOneField('journal.Issue', related_name='galley')

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
    account = models.ForeignKey('core.Account')
    issue = models.ForeignKey(Issue)
    role = models.CharField(max_length=255, default='Guest Editor')

    def __str__(self):
        return "{user} {role}".format(
            user=self.account.full_name(),
            role=self.role,
        )


class SectionOrdering(models.Model):
    section = models.ForeignKey('submission.Section')
    issue = models.ForeignKey(Issue)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return "{0}: {1}, ({2} {3}) {4}".format(self.order, self.issue.issue_title, self.issue.volume, self.issue.issue, self.section)

    class Meta:
        ordering = ('order', 'section')


class ArticleOrdering(models.Model):
    article = models.ForeignKey('submission.Article')
    issue = models.ForeignKey(Issue)
    section = models.ForeignKey('submission.Section')
    order = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('article', 'issue', 'section')
        ordering = ('order', 'section')

    def __str__(self):
        return "{0}: {1}, {2}".format(self.order, self.section, self.article.title)


class FixedPubCheckItems(models.Model):
    article = models.OneToOneField('submission.Article')

    metadata = models.BooleanField(default=False)
    verify_doi = models.BooleanField(default=False)
    select_issue = models.BooleanField(default=False)
    set_pub_date = models.BooleanField(default=False)
    notify_the_author = models.BooleanField(default=False)
    select_render_galley = models.BooleanField(default=False)
    select_article_image = models.BooleanField(default=False)


class PresetPublicationCheckItem(models.Model):
    journal = models.ForeignKey(Journal)

    title = models.TextField()
    text = models.TextField()
    enabled = models.BooleanField(default=True)


class PrePublicationChecklistItem(models.Model):
    article = models.ForeignKey('submission.Article')

    completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey('core.Account', blank=True, null=True)
    completed_on = models.DateTimeField(blank=True, null=True)

    title = models.TextField()
    text = models.TextField()

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
    journal = models.ForeignKey(Journal)
    user = models.ForeignKey('core.Account')
    domain = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=notification_type())
    active = models.BooleanField(default=False)

    def __str__(self):
        return '{0}, {1}: {2}'.format(self.journal, self.user, self.domain)


# Signals

@receiver(post_save, sender=Journal)
def setup_default_section(sender, instance, created, **kwargs):
    if created:
        submission_models.Section.objects.language('en').get_or_create(
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
def setup_default_form(sender, instance, created, **kwargs):
    if created:
        from review import models as review_models

        if not review_models.ReviewForm.objects.filter(
                slug='default-form',
                journal=instance,
        ).exists():

            default_review_form = review_models.ReviewForm.objects.create(
                journal=instance,
                name='Default Form',
                slug='default-form',
                intro='Please complete the form below.',
                thanks='Thank you for completing the review.'
            )

            main_element = review_models.ReviewFormElement.objects.create(
                name='Review',
                kind='textarea',
                required=True,
                order=1,
                width='large-12 columns',
                help_text='Please add as much detail as you can.'
            )

            default_review_form.elements.add(main_element)


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
                    )
                    ordering.delete()
                except ArticleOrdering.DoesNotExist:
                    pass

            elif action == 'post_add':
                ArticleOrdering.objects.get_or_create(
                    issue=issue,
                    article=article,
                    section=article.section,
                    order=issue.next_order(),
                )


m2m_changed.connect(issue_articles_change, sender=Issue.articles.through)

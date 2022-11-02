__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import json
import os
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core import models as core_models
from core.file_system import JanewayFileSystemStorage
from core.model_utils import AbstractSiteModel
from utils import logic
from utils.function_cache import cache
from utils.logger import get_logger


logger = get_logger(__name__)


fs = JanewayFileSystemStorage()


def cover_images_upload_path(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "press_carousel/"
    return os.path.join(path, filename)


def press_carousel_choices():
    return (
        ('articles', 'Latest Articles'),
        ('news', 'Latest News'),
        ('news_and_articles', 'Latest News and Articles')
    )


def press_text(type):
    path = os.path.join(
        settings.BASE_DIR, 'utils', 'install', 'press_text.json')
    with open(path, 'r', encoding="utf-8") as f:
        text = json.loads(f.read())[0]
        if type == 'registration':
            return text.get('registration')
        elif type == 'reset':
            return text.get('reset')
        else:
            return text.get(type)


class Press(AbstractSiteModel):
    name = models.CharField(max_length=600)
    thumbnail_image = models.ForeignKey(
        'core.File',
        null=True,
        blank=True,
        related_name='press_thumbnail_image',
        verbose_name='Press Logo',
        on_delete=models.SET_NULL,
    )
    footer_description = models.TextField(
        null=True,
        blank=True,
        help_text='Additional HTML for the press footer.',
    )
    main_contact = models.EmailField(default='janeway@voyager.com', blank=False, null=False)
    theme = models.CharField(max_length=255, default='OLH', blank=False, null=False)
    homepage_news_items = models.PositiveIntegerField(default=5)
    carousel_type = models.CharField(max_length=30, default='articles', choices=press_carousel_choices())
    carousel_items = models.PositiveIntegerField(default=4)
    carousel = models.OneToOneField(
        'carousel.Carousel',
        related_name='press',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    default_carousel_image = models.ImageField(upload_to=cover_images_upload_path, null=True, blank=True, storage=fs)
    favicon = models.ImageField(upload_to=cover_images_upload_path, null=True, blank=True, storage=fs)
    random_featured_journals = models.BooleanField(default=False)
    featured_journals = models.ManyToManyField('journal.Journal', blank=True, null=True)
    carousel_news_items = models.ManyToManyField('comms.NewsItem', blank=True, null=True)
    tracking_code = models.TextField(blank=True, null=True)
    privacy_policy_url = models.URLField(
        max_length=999, blank=True, null=True,
        help_text="URL to an external privacy-policy, linked from the page"
        " footer. If blank, it links to the Janeway CMS page: /site/privacy.",
    )

    password_reset_text = models.TextField(blank=True, null=True, default=press_text('reset'))
    registration_text = models.TextField(blank=True, null=True, default=press_text('registration'))

    password_number = models.BooleanField(default=False, help_text='If set, passwords must include one number.')
    password_upper = models.BooleanField(default=False, help_text='If set, passwords must include one upper case.')
    password_length = models.PositiveIntegerField(
        default=12,
        validators=[MinValueValidator(9)],
        help_text='The minimum length of an account password.',
    )

    enable_preprints = models.BooleanField(
        default=False,
        help_text='Enables the repository system for this press.',
        verbose_name='Enable repository system',
    )
    preprints_about = models.TextField(blank=True, null=True)
    preprint_start = models.TextField(blank=True, null=True)
    preprint_pdf_only = models.BooleanField(default=True, help_text='Forces manuscript files to be PDFs for Preprints.')
    preprint_submission = models.TextField(blank=True, null=True, default=press_text('submission'))
    preprint_publication = models.TextField(blank=True, null=True, default=press_text('publication'))
    preprint_decline = models.TextField(blank=True, null=True, default=press_text('decline'))

    random_homepage_preprints = models.BooleanField(default=False)
    homepage_preprints = models.ManyToManyField('submission.Article', blank=True)

    disable_journals = models.BooleanField(
        default=False,
        help_text='If enabled, the journals page will no longer render.'
    )

    def __str__(self):
        return u'%s' % self.name

    def __repr__(self):
        return u'%s' % self.name

    @staticmethod
    def get_press(request):
        try:
            p = Press.objects.all()[:1].get()
            return p
        except BaseException:
            return None

    @staticmethod
    def journals(**filters):
        from journal import models as journal_models
        if filters:
            return journal_models.Journal.objects.filter(**filters)
        return journal_models.Journal.objects.all()

    @staticmethod
    def users():
        return core_models.Account.objects.all()

    @property
    def issues(self, **filters):
        if not filters:
            filters = {}
        filters["journal__press"] = self
        from journal import models as journal_models
        if filters:
            return journal_models.Issue.objects.filter(**filters)
        return journal_models.Journal.objects.all()

    @staticmethod
    def users():
        return core_models.Account.objects.all()

    def journal_path_url(self, journal, path=None):
        """ Returns a Journal's path mode url relative to its press """
        return self.site_path_url(journal, path)

    def repository_path_url(self, repository, path=None):
        """ Returns a Repo's path mode url relative to its press """
        return self.site_path_url(repository, path)

    def site_path_url(self, child_site, path=None):
        """Returns the path mode URL of a site relative to its press"""
        _path = "/" + child_site.code
        request = logic.get_current_request()
        if settings.DEBUG and request:
            port = request.get_port()
        else:
            port = None
        if path is not None:
            # Ignore duplicate site code if provided in code
            if path.startswith(_path):
                path = path[len(_path):]
            _path += path

        return logic.build_url(
            netloc=self.domain,
            scheme=self.SCHEMES[self.is_secure],
            port=port,
            path=_path,
        )

    @staticmethod
    def press_cover(request, absolute=True):
        if request.press.thumbnail_image:
            if absolute:
                return os.path.join(settings.BASE_DIR, 'files', 'press',
                                    str(request.press.thumbnail_image.uuid_filename))
            else:
                return os.path.join('files', 'press', str(request.press.thumbnail_image.uuid_filename))
        else:
            return None

    @staticmethod
    def install_cover(press, request):
        """ Installs the default cover for the press (stored in Files/press/cover.png)

        :param press: the press object
        :param request: the current request or None
        :return: None
        """

        if request:
            owner = request.user if request.user is not None and not request.user.is_anonymous else core_models.Account(id=1)
        else:
            owner = core_models.Account(id=1)

        thumbnail_file = core_models.File(
            mime_type="image/png",
            original_filename="cover.png",
            uuid_filename="cover.png",
            label="Press logo",
            description="Logo for the press",
            owner=owner
        )

        core_models.File.add_root(instance=thumbnail_file)

        press.thumbnail_image = thumbnail_file
        press.save()

    def next_journal_order(self):
        from journal import models as journal_models
        max_number = max([journal.sequence for journal in journal_models.Journal.objects.all()])

        if not max_number:
            return 0
        else:
            return max_number + 1

    def next_contact_order(self):
        contacts = core_models.Contacts.objects.filter(content_type__model='press', object_id=self.pk)
        orderings = [contact.sequence for contact in contacts]
        return max(orderings) + 1 if orderings else 0

    @property
    def active_carousel(self):
        """ Renders a carousel for the journal homepage.
        :return: a tuple containing the active carousel and list of associated articles
        """
        if self.carousel is None or not self.carousel.enabled:
            return None, []
        items = self.carousel.get_items()

        return self.carousel, items

    def get_setting(self, name):
        return PressSetting.objects.get_or_create(press=self, name=name)

    def get_setting_value(self, name):
        try:
            return PressSetting.objects.get(press=self, name=name).value
        except PressSetting.DoesNotExist:
            return ''

    @property
    def publishes_conferences(self):
        return self.journals(is_conference=True).count() > 0

    @property
    def publishes_journals(self):
        return self.journals(is_conference=False).count() > 0

    @cache(600)
    def live_repositories(self):
        from repository import models as repository_models
        return repository_models.Repository.objects.filter(
            live=True,
        )

    @cache(600)
    def preprint_editors(self):
        from repository import models as repository_models
        editors = list()
        subjects = repository_models.Subject.objects.all()

        for subject in subjects:
            for editor in subject.editors.all():
                editors.append(editor)

        return set(editors)

    def preprint_dois_enabled(self):
        try:
            PressSetting.objects.get(press=self, name="Crossref Login")
        except PressSetting.DoesNotExist:
            return False

        try:
            PressSetting.objects.get(press=self, name="Crossref Password")
        except PressSetting.DoesNotExist:
            return False

        return True

    @property
    def code(self):
        return 'press'

    class Meta:
        verbose_name_plural = 'presses'


class PressSetting(models.Model):
    press = models.ForeignKey(Press)
    name = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)
    is_boolean = models.BooleanField(default=False)

    def __str__(self):
        return '{name} - {press}'.format(name=self.name, press=self.press.name)

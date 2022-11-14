__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os
import uuid
from dateutil import parser as dateparser

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.shortcuts import reverse
from django.http.request import split_domain_port

from core.file_system import JanewayFileSystemStorage
from core import model_utils, files, models as core_models
from utils import logic, models as utils_models
from repository import install
from utils.function_cache import cache
from submission import models as submission_models
from events import logic as event_logic


STAGE_PREPRINT_UNSUBMITTED = 'preprint_unsubmitted'
STAGE_PREPRINT_REVIEW = 'preprint_review'
STAGE_PREPRINT_PUBLISHED = 'preprint_published'
STAGE_PREPRINT_REJECTED = 'preprint_rejected'

SUBMITTED_STAGES = {
    STAGE_PREPRINT_REVIEW,
    STAGE_PREPRINT_PUBLISHED,
    STAGE_PREPRINT_REJECTED
}


def html_input_types():
    return (
        ('text', 'Text'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('textarea', 'Text Area'),
    )


def width_choices():
    return (
        (3, '3'),
        (6, '6'),
        (9, '9'),
        (12, '12'),
    )


fs_path = os.path.join('files/')
preprint_file_store = JanewayFileSystemStorage(location=fs_path)
preprint_media_store = JanewayFileSystemStorage()


def preprint_file_upload(instance, filename):
    try:
        uuid_filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        uuid_filename = str(uuid.uuid4())

    path = os.path.join('repos', str(instance.preprint.pk), uuid_filename)
    instance.original_filename = filename
    return path


def repo_media_upload(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "repos/{0}/".format(instance.pk)
    return os.path.join(path, filename)


class Repository(model_utils.AbstractSiteModel):
    press = models.ForeignKey('press.Press')
    name = models.CharField(max_length=255)
    short_name = models.CharField(
        max_length=15,
        help_text='Shortened version of the name eg. olh. Max 15 chars.'
    )
    object_name = models.CharField(
        max_length=255,
        help_text='eg. preprint or article',
    )
    object_name_plural = models.CharField(
        max_length=255,
        help_text='eg. preprints or articles',
    )
    managers = models.ManyToManyField('core.Account', blank=True)
    submission_notification_recipients = models.ManyToManyField('core.Account', blank=True, related_name='submission_notification_repositories')
    logo = model_utils.SVGImageField(
        blank=True,
        null=True,
        storage=preprint_media_store,
        upload_to=repo_media_upload,
    )
    favicon = models.ImageField(
        blank=True,
        null=True,
        storage=preprint_media_store,
        upload_to=repo_media_upload,
    )
    hero_background = model_utils.SVGImageField(
        blank=True,
        null=True,
        storage=preprint_media_store,
        upload_to=repo_media_upload,
    )
    publisher = models.CharField(
        max_length=255,
        help_text=_('Used for outputs including DC and Citation metadata'),
    )
    custom_js_code = models.TextField(
        blank=True,
        null=True,
        help_text=_('The contents of this field are output into the JS area'
                    'at the foot of every Repository page.')
    )
    live = models.BooleanField(
        default=False,
        verbose_name='Repository is Live?'
    )
    limit_upload_to_pdf = models.BooleanField(
        default=False,
        help_text=_('If set to True, this will require all file uploads from'
                    'authors to be PDF files.')
    )
    about = models.TextField(blank=True, null=True)
    start = models.TextField(
        blank=True,
        null=True,
        verbose_name='Submission Start Text',
    )
    submission = models.TextField(blank=True, null=True)
    publication = models.TextField(blank=True, null=True)
    decline = models.TextField(blank=True, null=True)
    accept_version = models.TextField(blank=True, null=True)
    decline_version = models.TextField(blank=True, null=True)
    new_comment = models.TextField(blank=True, null=True)
    review_invitation = models.TextField(blank=True, null=True)
    review_helper = models.TextField(blank=True, null=True)
    manager_review_status_change = models.TextField(blank=True, null=True)
    reviewer_review_status_change = models.TextField(blank=True, null=True)
    footer = models.TextField(
        blank=True,
        null=True,
        default='<p>Powered by Janeway</p>',
    )
    login_text = models.TextField(
        blank=True,
        null=True,
        help_text='If text is added it will display on the login '
                  'and register pages.',
        verbose_name='Account Page Text'
    )
    submission_agreement = models.TextField(
        null=True,
        help_text="Add any information that the author may need to know as "
                  "part of their submission, eg. Copyright transfer etc.'",
        default="<p>Authors grant us the right to publish, on this website, "
                "their uploaded manuscript, supplementary materials and "
                "any supplied metadata.</p>",
    )

    random_homepage_preprints = models.BooleanField(default=False)
    homepage_preprints = models.ManyToManyField(
        'submission.Article',
        blank=True,
    )
    limit_access_to_submission = models.BooleanField(
        default=False,
        help_text='If enabled, users need to request access to submit preprints.',
    )
    submission_access_request_text = models.TextField(
        blank=True,
        null=True,
        help_text='Describe any supporting information you want users to supply when requesting'
                  'access permissions for this repository. Linked to Limit Access to Submissions.',
    )
    submission_access_contact = models.EmailField(
        blank=True,
        null=True,
        help_text='Will be notified of new submission access requests.',
    )
    active_licenses = models.ManyToManyField(
        'submission.Licence',
        blank=True,
    )

    class Meta:
        verbose_name_plural = 'repositories'

    @classmethod
    def get_by_request(cls, request):
        obj, path = super().get_by_request(request)
        if not obj:
            # Lookup by short_name
            try:
                short_name = request.path.split('/')[1]
                obj = cls.objects.get(short_name=short_name)
                path = short_name
            except (IndexError, cls.DoesNotExist):
                pass
        return obj, path

    def __str__(self):
        return '[{}] {}'.format(
            'live' if self.live else 'disabled',
            self.name,
        )

    def top_level_subjects(self):
        return Subject.objects.filter(
            repository=self,
            parent=None,
        ).prefetch_related(
            'children'
        )

    def additional_submission_fields(self):
        return RepositoryField.objects.filter(
            repository=self,
        )

    def site_url(self, path=""):
        if self.domain and not settings.URL_CONFIG == 'path':
            return logic.build_url(
                    netloc=self.domain,
                    scheme=self.SCHEMES[self.is_secure],
                    port=None,
                    path=path,
            )
        else:
            return self.press.site_path_url(self, path)

    @property
    def code(self):
        return self.short_name

    def reviewer_accounts(self):
        reviewer_ids = RepositoryRole.objects.filter(
            repository=self,
            role__slug='reviewer',
        ).values_list('user__id')
        return core_models.Account.objects.filter(
            pk__in=reviewer_ids,
        )


class RepositoryRole(models.Model):
    repository = models.ForeignKey(Repository)
    user = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        'core.Role',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return 'User {} registered as {} on Repo {}'.format(
            self.user.full_name(),
            self.role,
            self.repository.name,
        )


class RepositoryField(models.Model):
    repository = models.ForeignKey(Repository)
    name = models.CharField(max_length=255)
    input_type = models.CharField(
        max_length=255,
        choices=html_input_types(),
    )
    choices = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text='Separate choices with the bar | character.',
    )
    required = models.BooleanField(default=True)
    order = models.IntegerField()
    help_text = models.TextField(blank=True, null=True)
    display = models.BooleanField(
        default=False,
        help_text='Whether or not display this field in the article page',
    )
    dc_metadata_type = models.CharField(
        max_length=255,
        help_text=_(
            'If this field is to be output as a dc metadata field you can add'
            'the type here.'
        ),
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('order', 'name',)

    def __str__(self):
        return '{}: {}'.format(self.repository.name, self.name)


class RepositoryFieldAnswer(models.Model):
    field = models.ForeignKey(
        RepositoryField,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    preprint = models.ForeignKey('Preprint')
    answer = models.TextField()

    def __str__(self):
        return '{}: {}'.format(self.preprint, self.answer)


class Preprint(models.Model):
    repository = models.ForeignKey(
        Repository,
        null=True,
        on_delete=models.SET_NULL,
    )
    owner = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
        help_text='The account that submitted this item.',
    )
    stage = models.CharField(max_length=25, default=STAGE_PREPRINT_UNSUBMITTED)
    title = models.CharField(
        max_length=300,
        help_text=_('Your article title'),
    )
    abstract = models.TextField(
        blank=True,
        null=True,
        help_text=_(
            'Please avoid pasting content from word processors as they can add '
            'unwanted styling to the abstract. You can retype the abstract '
            'here or copy and paste it into notepad/a plain text editor before '
            'pasting here.',
        )

    )
    submission_file = models.ForeignKey(
        'PreprintFile',
        related_name='submission_file',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    meta_image = models.ImageField(
        blank=True,
        null=True,
        upload_to=preprint_file_upload,
        storage=preprint_media_store,
    )
    subject = models.ManyToManyField(
        'Subject',
        blank=False,
        null=True,
    )
    keywords = model_utils.M2MOrderedThroughField(
        "submission.Keyword",
        blank=True, null=True, through='repository.KeywordPreprint',
    )
    license = models.ForeignKey(
        'submission.Licence',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    comments_editor = models.TextField(
        blank=True,
        null=True,
        verbose_name="Comments to the Editor",
        help_text="Add any comments you'd like the editor to consider here.",
    )
    doi = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Published DOI',
        help_text='You can add a DOI linking to this item\'s published version using this field. '
                  'Please provide the full DOI ie. https://doi.org/10.1017/CBO9781316161012.'
    )
    preprint_doi = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Preprint DOI',
        help_text='System supplied DOI. '
    )
    preprint_decline_note = models.TextField(
        blank=True,
        null=True,
    )
    preprint_decision_notification = models.BooleanField(
        default=False,
    )
    date_started = models.DateTimeField(default=timezone.now)
    date_submitted = models.DateTimeField(blank=True, null=True)
    date_accepted = models.DateTimeField(blank=True, null=True)
    date_declined = models.DateTimeField(blank=True, null=True)
    date_published = models.DateTimeField(blank=True, null=True)
    date_updated = models.DateTimeField(blank=True, null=True)
    current_step = models.IntegerField(default=1)

    article = models.OneToOneField(
        'submission.Article',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Linked article of this preprint.',
    )

    def __str__(self):
        return '{}'.format(
            self.title,
        )

    def old_versions(self):
        return PreprintVersion.objects.filter(
            preprint=self,
        ).exclude(
            preprint=self.current_version,
        )

    @property
    def current_version(self):
        try:
            return self.preprintversion_set.all()[0]
        except IndexError:
            return None

    def version_files(self):
        return [
            version.file for version in self.preprintversion_set.filter(
                Q(moderated_version__approved=True) | Q(moderated_version__isnull=True)
            )
        ]

    @property
    @cache(300)
    def views(self):
        return PreprintAccess.objects.filter(
            preprint=self,
            file__isnull=True
        )

    @property
    @cache(300)
    def downloads(self):
        return PreprintAccess.objects.filter(
            preprint=self,
            file__isnull=False,
        )

    def next_author_order(self):
        try:
            last_author = self.preprintauthor_set.all().reverse()[0]
            return last_author.order + 1
        except IndexError:
            return 0

    def next_version_number(self):
        try:
            last_version = self.preprintversion_set.all()[0]
            return last_version.version + 1
        except IndexError:
            return 1

    @property
    def authors(self):
        preprint_authors = PreprintAuthor.objects.filter(
            preprint=self,
        ).select_related('account')

        return [pa.account for pa in preprint_authors]

    @property
    def supplementaryfiles(self):
        return PreprintSupplementaryFile.objects.filter(
            preprint=self,
        )

    def author_objects(self):
        pks = [author.account.pk for author in self.authors]
        return core_models.Account.objects.filter(pk__in=pks)

    def display_authors_compact(self):
        etal = ", ".join([author.full_name() for author in self.authors[:3]])
        if len(self.authors) > 3:
            etal = etal + ", et al."
        return etal

    def display_authors(self):
        return ", ".join([author.full_name() for author in self.authors if author is not None])

    def add_user_as_author(self, user):
        preprint_author, created = PreprintAuthor.objects.get_or_create(
            account=user,
            affiliation=user.institution,
            preprint=self,
            defaults={'order': self.next_author_order()},
        )

        return created

    def add_author(self, author):
        preprint_author, created = PreprintAuthor.objects.get_or_create(
            author=author,
            preprint=self,
            order=self.next_author_order(),
        )

        return preprint_author, created

    def add_supplementary_file(self, supplementary):
        return PreprintSupplementaryFile.objects.get_or_create(
            label=supplementary.cleaned_data['label'],
            url=supplementary.cleaned_data['url'],
            preprint=self,
            defaults={
                'order': self.next_supp_file_order()
            },
        )

    def next_supp_file_order(self):
        orderings = [supp_file.order for supp_file in self.supplementaryfiles]
        return max(orderings) + 1 if orderings else 0

    def user_is_author(self, user):
        if user.email in [author.email for author in self.authors]:
            return True

        return False

    def set_file(self, file, original_filename):
        self.submission_file.original_filename = original_filename
        self.submission_file.file = file
        self.submission_file.save()

    def submit_preprint(self):
        self.date_submitted = timezone.now()
        self.stage = STAGE_PREPRINT_REVIEW
        self.current_step = 5
        self.save()

    def subject_editors(self):
        editors = []
        for subject in self.subject.all():
            for editor in subject.editors.all():
                editors.append(editor)

        return editors

    def has_version(self):
        return self.preprintversion_set.all()

    def additional_field_answers(self):
        return self.repositoryfieldanswer_set.all()

    def display_additional_fields(self):
        return self.repositoryfieldanswer_set.filter(
            field__display=True,
        )

    def make_new_version(self, file):
        PreprintVersion.objects.create(
            preprint=self,
            file=file,
            version=self.next_version_number(),
        )

    def update_date_published(self, date, time):
        self.date_published = dateparser.parse(
            '{date} {time}'.format(
                date=date,
                time=time,
            )
        )
        self.save()

    def accept(self, date, time):
        self.date_accepted = timezone.now()
        self.date_declined = None
        self.stage = STAGE_PREPRINT_PUBLISHED
        self.date_published = dateparser.parse(
            '{date} {time}'.format(
                date=date,
                time=time,
            )
        )
        self.save()

    def decline(self, note):
        self.date_declined = timezone.now()
        self.date_accepted = None
        self.stage = STAGE_PREPRINT_REJECTED
        self.preprint_decline_note = note
        self.save()

    def reset(self):
        self.date_accepted = None
        self.date_declined = None
        self.date_published = None
        self.preprint_decision_notification = False
        self.stage = STAGE_PREPRINT_REVIEW
        self.preprint_decline_note = None
        self.save()

    def is_published(self):
        if self.stage == STAGE_PREPRINT_PUBLISHED and self.date_published:
            return True
        return False

    def current_version_file_type(self):
        if self.current_version.file.mime_type in files.HTML_MIMETYPES:
            return 'html'
        elif self.current_version.file.mime_type in files.PDF_MIMETYPES:
            return 'pdf'
        return None

    @property
    @cache(600)
    def url(self):
        return self.repository.site_url(path=self.local_url)

    @property
    def local_url(self):
        url = reverse(
            'repository_preprint',
            kwargs={'preprint_id': self.id,}
        )

        return url

    def create_article(self, journal, workflow_stage, journal_license, journal_section, force=False):
        """
        Creates an article in a given journal and workflow stage.
        """
        if not self.article or force:
            # create base article
            article = submission_models.Article.objects.create(
                journal=journal,
                owner=self.owner,
                title=self.title,
                abstract=self.abstract,
                license=journal_license,
                section=journal_section,
                date_submitted=timezone.now(),
                comments_editor='Submitted from {}'.format(self.repository.name),
                stage=workflow_stage,
            )

            # copy authors to submission
            for preprint_author in self.preprintauthor_set.all():
                submission_models.ArticleAuthorOrder.objects.get_or_create(
                    article=article,
                    author=preprint_author.account,
                    defaults={
                        'order': preprint_author.order
                    }
                )
                article.authors.add(preprint_author.account)

            # snapshot authors
            article.snapshot_authors()

            # copy preprints latest file and add it as a MS file to the article
            file = files.copy_preprint_file_to_article(
                self,
                article,
                manuscript=True,
            )

            # save and return the article
            self.article = article
            self.save()
            return article

        # Return None to indicate this method has not created a new article object.
        return None


class KeywordPreprint(models.Model):
    keyword = models.ForeignKey("submission.Keyword")
    preprint = models.ForeignKey(Preprint)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        unique_together = ('keyword', 'preprint')

    def __str__(self):
        return self.keyword.word

    def __repr__(self):
        return "KeywordPreprint(%s, %d)" % (self.keyword.word, self.preprint.id)


class PreprintFile(models.Model):
    preprint = models.ForeignKey(Preprint)
    file = models.FileField(
        upload_to=preprint_file_upload,
        storage=preprint_file_store,
    )
    original_filename = models.TextField()
    uploaded = models.DateTimeField(default=timezone.now)
    mime_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    size = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.original_filename

    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def uuid_filename(self):
        return self.filename()

    def get_file_mime_type(self):
        return files.file_path_mime(self.file.path)

    def path_parts(self):
        path = os.path.dirname(os.path.abspath(self.file.path))
        return path

    def reverse_kwargs(self):
        return {
            'preprint_id': self.preprint.pk,
            'file_id': self.pk,
        }

    def download_url(self):
        return reverse(
            'repository_download_file',
            kwargs=self.reverse_kwargs(),
        )

    def contents(self):
        file = open(self.file.path, mode='r')
        contents = file.read()
        file.close()
        return contents


class PreprintSupplementaryFile(models.Model):
    preprint = models.ForeignKey(Preprint)
    url = models.URLField()
    label = models.CharField(max_length=200, verbose_name=_('Label'), default='Supplementary File')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('order',)
        unique_together = ('url', 'preprint')


class PreprintAccess(models.Model):
    preprint = models.ForeignKey(Preprint)
    file = models.ForeignKey(PreprintFile, blank=True, null=True)
    identifier = models.TextField(blank=True, null=True)
    accessed = models.DateTimeField(auto_now_add=True)
    country = models.ForeignKey('core.Country', blank=True, null=True)

    @property
    def access_type(self):
        if self.file:
            return 'download'
        return 'view'


class PreprintAuthorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('author')


class PreprintAuthor(models.Model):
    preprint = models.ForeignKey('Preprint')
    account = models.ForeignKey('core.Account', null=True)
    author = models.ForeignKey('Author', blank=True, null=True)  # Author is no longer in use, it will be removed.
    order = models.PositiveIntegerField(default=0)
    objects = PreprintAuthorManager()
    affiliation = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ('order',)
        unique_together = ('account', 'preprint')

    def __str__(self):
        return '{author} linked to {preprint}'.format(
            author=self.account.full_name() if self.account else '',
            preprint=self.preprint.title,
        )

    @property
    def full_name(self):
        if not self.account.middle_name:
            return '{} {}'.format(self.account.first_name, self.account.last_name)
        else:
            return '{} {} {}'.format(
                self.account.first_name,
                self.account.middle_name,
                self.account.last_name,
            )

    def dc_name(self):
        if not self.account.middle_name:
            return '{}, {}'.format(self.account.last_name, self.account.first_name)
        else:
            return '{}. {} {}'.format(
                self.account.last_name,
                self.account.first_name,
                self.account.middle_name,
            )

    def to_dc(self):
        return '<meta name="DC.Contributor" content="{}">'.format(
            self.dc_name,
        )

    def display_affiliation(self):
        if self.affiliation:
            return self.affiliation
        if self.account is not None:
            return self.account.institution


class Author(models.Model):
    email_address = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    affiliation = models.TextField(blank=True, null=True)
    orcid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('ORCID')
    )

    @property
    def full_name(self):
        if not self.middle_name:
            return '{} {}'.format(self.first_name, self.last_name)
        else:
            return '{} {} {}'.format(
                self.first_name,
                self.middle_name,
                self.last_name,
            )


class PreprintVersion(models.Model):
    preprint = models.ForeignKey(Preprint)
    file = models.ForeignKey(PreprintFile)
    version = models.IntegerField(default=1)
    date_time = models.DateTimeField(default=timezone.now)
    moderated_version = models.ForeignKey(
        'VersionQueue',
        blank=True,
        null=True,
    )
    title = models.CharField(
        max_length=300,
        help_text=_('Your article title'),
    )
    abstract = models.TextField(
        blank=True,
        null=True,
        help_text=_(
            'Please avoid pasting content from word processors as they can add '
            'unwanted styling to the abstract. You can retype the abstract '
            'here or copy and paste it into notepad/a plain text editor before '
            'pasting here.',
        )

    )
    published_doi = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Published Article DOI",
        help_text="Please use the following format for your DOI: https://doi.org/10.xxxx/xxxx",
    )

    class Meta:
        ordering = ('-version', '-date_time', '-id')

    def html(self):
        if self.file.mime_type in files.HTML_MIMETYPES:
            return self.file.contents()
        else:
            return ''


class Comment(models.Model):
    author = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
    )
    preprint = models.ForeignKey(
        Preprint,
        null=True,
        on_delete=models.SET_NULL,
    )
    reply_to = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    date_time = models.DateTimeField(default=timezone.now)
    body = models.TextField(verbose_name='Write your comment:')
    is_reviewed = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ('-date_time', '-pk')

    def __str__(self):
        return 'Comment by {author} on {article}'.format(
            author=self.author.full_name(),
            article=self.preprint.title,
        )
    
    def toggle_public(self):
        if self.is_public:
            self.is_public = False
        else:
            self.is_public = True

        self.is_reviewed = True
        self.save()

    def mark_reviewed(self):
        self.is_reviewed = True
        self.save()


class Subject(models.Model):
    repository = models.ForeignKey(Repository)
    name = models.CharField(max_length=255)
    slug = models.SlugField(blank=True, max_length=255)
    editors = models.ManyToManyField('core.Account', blank=True)
    enabled = models.BooleanField(
        default=True,
        help_text='If disabled, this subject will not appear publicly.',
    )
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='children',
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ('slug', 'pk')

    def __str__(self):
        return self.name

    def published_preprints(self):
        return self.preprint_set.filter(
            repository=self.repository,
            stage=STAGE_PREPRINT_PUBLISHED,
        )

    def published_preprints_count(self):
        return self.published_preprints().count()


def version_choices():
    return (
        ('correction', 'Text Correction'),
        ('metadata_correction', 'Metadata Correction'),
        ('version', 'New Version'),
    )


class VersionQueue(models.Model):
    preprint = models.ForeignKey(Preprint)
    file = models.ForeignKey(PreprintFile, null=True)
    update_type = models.CharField(max_length=20, choices=version_choices())

    date_submitted = models.DateTimeField(default=timezone.now)
    date_decision = models.DateTimeField(blank=True, null=True)
    approved = models.BooleanField(default=False)

    published_doi = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Published Article DOI",
        help_text="Please use the following format for your DOI: https://doi.org/10.xxxx/xxxx",
    )

    title = models.CharField(
        max_length=300,
        help_text=_('Your article title'),
    )
    abstract = models.TextField(
        blank=True,
        null=True,
        help_text=_(
            'Please avoid pasting content from word processors as they can add '
            'unwanted styling to the abstract. You can retype the abstract '
            'here or copy and paste it into notepad/a plain text editor before '
            'pasting here.',
        )

    )

    def approve(self):
        self.date_decision = timezone.now()
        self.approved = True
        current_version = None

        # Update the current version to have the Preprint's current title
        # and abstract.
        if self.preprint.current_version is not None:
            current_version = self.preprint.current_version
            current_version.title = self.preprint.title
            current_version.abstract = self.preprint.abstract
            current_version.published_doi = self.preprint.doi
            this_file = self.preprint.current_version.file
        # no version yet
        else:
            this_file = self.preprint.submission_file

        # Create a new PreprintVersion, this will now be the current_version.
        # If the current VersionQueue has no file (in the case of Metadata
        # updates) use the preprint's current version's file.
        PreprintVersion.objects.create(
            preprint=self.preprint,
            file=self.file if self.file else this_file,
            version=self.preprint.next_version_number(),
            moderated_version=self,
            published_doi=self.published_doi,
        )

        # Overwrite the preprint's metadata now we have a historical record.
        # Check that title and abstract have value, if not there is no change.
        if self.title:
            self.preprint.title = self.title
        if self.abstract:
            self.preprint.abstract = self.abstract
        if self.published_doi:
            self.preprint.doi = self.published_doi

        if current_version is not None:
            current_version.save()
        self.preprint.save()
        self.save()

    def decline(self):
        self.date_decision = timezone.now()
        self.approved = False
        self.save()

    def decision(self):
        if self.date_decision and self.approved:
            return True
        elif self.date_decision:
            return False

    def status(self):
        if self.date_decision and self.approved:
            return _('Approved')
        elif not self.date_decision:
            return _('Under Review')
        else:
            return _('Declined')


def review_status_choices():
    return (
        ('new', 'New'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('complete', 'Complete'),
        ('withdrawn', 'Withdrawn'),
    )


class Review(models.Model):
    preprint = models.ForeignKey(
        'Preprint',
        on_delete=models.CASCADE,
    )
    manager = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
        related_name='review_manager',
        help_text='The manager making the review request.',
    )
    reviewer = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
        related_name='review_reviewer',
    )
    date_assigned = models.DateTimeField(
        blank=True,
        null=True,
        auto_now_add=True,
    )
    date_due = models.DateField(
        blank=True,
        null=True,
        verbose_name="Due date",
    )
    date_accepted = models.DateTimeField(
        blank=True,
        null=True,
    )
    date_completed = models.DateTimeField(
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=10,
        choices=review_status_choices(),
    )
    access_code = models.UUIDField(
        default=uuid.uuid4,
    )
    comment = models.OneToOneField(
        'Comment',
        blank=True,
        null=True,
    )
    anonymous = models.BooleanField(
        default=False,
    )
    status_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Information supplied by a reviewer when declining or completing '
                  'a review or by staff withdrawing a review',
    )
    notification_sent = models.BooleanField(
        default=False,
    )

    def accept(self, request):
        self.date_accepted = timezone.now()
        self.status = 'accepted'
        self.save()

        # Raise event
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_REVIEW_STATUS_CHANGE,
            **{
                'request': request,
                'review': self,
                'status_change': 'accept',
            }
        )

    def decline(self, request):
        self.date_completed = timezone.now()
        self.status = 'declined'
        self.save()

        # Raise event
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_REVIEW_STATUS_CHANGE,
            **{
                'request': request,
                'review': self,
                'status_change': 'decline',
            }
        )

    def complete(self, request):
        self.date_completed = timezone.now()
        self.status = 'complete'
        self.save()

        # Raise event
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_REVIEW_STATUS_CHANGE,
            **{
                'request': request,
                'review': self,
                'status_change': 'complete',
            }
        )

    def withdraw(self, reason, request):
        self.date_completed = timezone.now()
        self.status = 'withdrawn'
        self.status_reason = reason
        self.save()

        # Raise event
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_REVIEW_STATUS_CHANGE,
            **{
                'request': request,
                'review': self,
                'status_change': 'withdraw',
            }
        )

    def reset(self, user):
        self.date_accepted = None
        self.date_completed = None
        self.status = 'new'
        self.status_reason = 'Invited Review reset by staff.'
        self.save()

        utils_models.LogEntry.add_entry(
            types='Preprint Review',
            description='Preprint Review by {} reset'.format(self.reviewer.full_name()),
            level='Info',
            actor=user,
            target=self.preprint,
        )

    def publish(self, user=None):
        if self.comment:
            self.comment.is_reviewed = True
            self.comment.is_public = True
            self.comment.save()

            utils_models.LogEntry.add_entry(
                types='Preprint Review',
                description='Preprint Review by {} published'.format(self.reviewer.full_name()),
                level='Info',
                actor=user,
                target=self.preprint,
            )

    def unpublish(self, user):
        if self.comment:
            self.comment.is_public = False
            self.comment.save()

            utils_models.LogEntry.add_entry(
                types='Preprint Review',
                description='Preprint Review by {} unpublished'.format(self.reviewer.full_name()),
                level='Info',
                actor=user,
                target=self.preprint,
            )


@receiver(models.signals.post_delete, sender=PreprintFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `PreprintFile` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            try:
                os.remove(instance.file.path)
            except FileNotFoundError:
                pass


@receiver(models.signals.pre_save, sender=PreprintFile)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `PreprintFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = PreprintFile.objects.get(pk=instance.pk).file
    except PreprintFile.DoesNotExist:
        return False

    new_file = instance.file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(models.signals.pre_save, sender=Repository)
def add_email_setting_defaults(sender, instance, **kwargs):
    """
    When a new Repository is added we insert the email settings onto the
    instance before it is saved.
    """
    if instance._state.adding:
        install.load_settings(instance)

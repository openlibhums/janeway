__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os
import uuid

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from core.file_system import JanewayFileSystemStorage


def html_input_types():
    return (
        ('text', 'Text'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('number', 'Number'),
        ('date', 'Date'),
    )


def width_choices():
    return (
        (3, '3'),
        (6, '6'),
        (9, '9'),
        (12, '12'),
    )


fs_path = os.path.join(settings.BASE_DIR, 'files')
preprint_file_store = JanewayFileSystemStorage(location=fs_path )
preprint_media_store = JanewayFileSystemStorage()


def preprint_file_upload(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "preprints/{0}/".format(instance.pk)
    return os.path.join(path, filename)


class Repository(models.Model):
    name = models.CharField(max_length=255)
    managers = models.ManyToManyField('core.Account')
    logo = models.ImageField(
        blank=True,
        null=True,
        upload_to=preprint_media_store,
        storage=preprint_media_store,
    )
    publisher = models.CharField(
        max_length=255,
        help_text=_('Used for outputs including DC and Citation metadata'),
    )
    live = models.BooleanField(default=False)


class RepositoryFields(models.Model):
    repository = models.ForeignKey(Repository)
    name = models.CharField(max_length=255)
    input_type = models.CharField(
        max_length=255,
        choices=html_input_types(),
    )
    width = models.CharField(
        max_length=2,
        choices=width_choices(),
    )
    dc_metadata_type = models.CharField(
        max_length=255,
        help_text=_(
            'If this field is to be output as a dc metadata field you can add'
            'the type here.'
        ),
    )


class Preprint(models.Model):
    repository = models.ForeignKey(Repository)
    owner = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
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
    submission_file = models.ForeignKey(
        'PreprintFile',
        related_name='submission_file',
    )
    meta_image = models.ImageField(
        blank=True,
        null=True,
        upload_to=preprint_file_upload,
        storage=preprint_media_store,
    )
    subject = models.ForeignKey('Subject')
    keywords = models.ManyToManyField(
        'submission.Keyword',
        blank=True,
        null=True,
    )
    license = models.ForeignKey(
        'submission.Licence',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    doi = models.CharField(
        max_length=100,
    )
    curent_version = models.ForeignKey(
        'PreprintVersion',
        related_name='curent_version',
    )
    preprint_decision_notification = models.BooleanField(
        default=False,
    )
    date_started = models.DateTimeField(auto_now_add=True)
    date_submitted = models.DateTimeField(blank=True, null=True)
    date_accepted = models.DateTimeField(blank=True, null=True)
    date_declined = models.DateTimeField(blank=True, null=True)
    date_published = models.DateTimeField(blank=True, null=True)
    date_updated = models.DateTimeField(blank=True, null=True)
    current_step = models.IntegerField(default=1)

    def old_versions(self):
        return PreprintVersion.objects.filter(
            preprint=self,
        ).exclude(
            preprint=self.curent_version,
        )

    @property
    def views(self):
        return PreprintAccess.objects.filter(
            preprint=self,
            file__isnull=True
        )

    @property
    def downloads(self):
        return PreprintAccess.objects.filter(
            preprint=self,
            file__isnull=False,
        )


class PreprintFile(models.Model):
    preprint = models.ForeignKey(Preprint)
    file = models.FileField(
        upload_to=preprint_file_upload,
        storage=preprint_file_store,
    )


class PreprintAccess(models.Model):
    preprint = models.ForeignKey(Preprint)
    file = models.ForeignKey(PreprintFile, blank=True, null=True)
    dt = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=10)
    

class Author(models.Model):
    preprint = models.ForeignKey(Preprint)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    affiliation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.full_name

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

    def dc_name(self):
        if not self.middle_name:
            return '{}, {}'.format(self.last_name, self.first_name)
        else:
            return '{}. {} {}'.format(
                self.last_name,
                self.first_name,
                self.middle_name,
            )

    def to_dc(self):
        return '<meta name="DC.Contributor" content="{}">'.format(
            self.dc_name,
        )


class PreprintVersion(models.Model):
    preprint = models.ForeignKey(Preprint)
    file = models.ForeignKey(PreprintFile)
    version = models.IntegerField(default=1)
    date_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('-date_time', '-id')


class Comment(models.Model):
    author = models.ForeignKey('core.Account')
    preprint = models.ForeignKey(Preprint)
    reply_to = models.ForeignKey('self', blank=True, null=True)
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


class Subject(models.Model):
    repository = models.ForeignKey(Repository)
    name = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    editors = models.ManyToManyField('core.Account')
    enabled = models.BooleanField(
        default=True,
        help_text='If disabled, this subject will not appear publicly.',
    )
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='children',
    )

    class Meta:
        ordering = ('slug', 'pk')

    def __str__(self):
        return self.name


def version_choices():
    return (
        ('correction', 'Correction'),
        ('version', 'New Version'),
    )


class VersionQueue(models.Model):
    preprint = models.ForeignKey(Preprint)
    file = models.ForeignKey(PreprintFile)
    update_type = models.CharField(max_length=10, choices=version_choices())

    date_submitted = models.DateTimeField(default=timezone.now)
    date_decision = models.DateTimeField(blank=True, null=True)
    approved = models.BooleanField(default=False)

    def decision(self):
        if self.date_decision and self.approved:
            return True
        elif self.date_decision:
            return False

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json as jason
import os
from uuid import uuid4
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from django.utils import timezone
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from django.utils.text import slugify

from utils.shared import get_ip_address, join_lists
from utils.importers.up import get_input_value_by_name


LOG_TYPES = [
    ('Email', 'Email'),
    ('PageView', 'PageView'),
    ('EditorialAction', 'EditorialAction'),
    ('Error', 'Error'),
    ('Authentication', 'Authentication'),
    ('Submission', 'Submission'),
    ('Publication', 'Publication')
]

LOG_LEVELS = [
    ('Error', 'Error'),
    ('Debug', 'Debug'),
    ('Info', 'Info'),
]

MESSAGE_STATUS = [
    ('no_information', 'No Information'),
    ('accepted', 'Sending'),
    ('delivered', 'Delivered'),
    ('failed', 'Failed'),
]


class LogEntry(models.Model):
    types = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    subject = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    level = models.CharField(max_length=20, null=True, blank=True, choices=LOG_LEVELS)
    actor = models.ForeignKey('core.Account', null=True, blank=True, related_name='actor', on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, related_name='content_type', null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    target = GenericForeignKey('content_type', 'object_id')

    is_email = models.BooleanField(default=False)
    email_subject = models.TextField(blank=True, null=True)
    message_id = models.TextField(blank=True, null=True)
    message_status = models.CharField(max_length=255, choices=MESSAGE_STATUS, default='no_information')
    number_status_checks = models.IntegerField(default=0)
    status_checks_complete = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'log entries'

    def __str__(self):
        return u'[{0}] {1} - {2} {3}'.format(self.types, self.date, self.subject, self.message_id)

    def __repr__(self):
        return u'[{0}] {1} - {2} {3}'.format(self.types, self.date, self.subject, self.message_id)

    def message_status_class(self):
        if self.message_status == 'delivered':
            return 'green'
        elif self.message_status == 'failed':
            return 'red'
        else:
            return 'amber'

    @property
    def to(self):
        return [to.email for to in self.toaddress_set.all()]

    @staticmethod
    def add_entry(
            types,
            description,
            level,
            actor=None,
            request=None,
            target=None,
            is_email=False,
            to=None,
            message_id=None,
            subject=None,
            email_subject=None,
            cc=None,
            bcc=None
    ):

        # When a user is not logged in request.user is a SimpleLazyObject
        # so we check if the actor is_anonymous.
        if actor is not None and actor.is_anonymous:
            actor = None

        kwargs = {
            'types': types,
            'description': description,
            'level': level,
            # if no actor is supplied, assume anonymous
            'actor': actor if actor else None,
            'ip_address': get_ip_address(request),
            'target': target,
            'is_email': is_email,
            'message_id': message_id,
            'subject': subject,
            'email_subject': email_subject,
        }
        new_entry = LogEntry.objects.create(**kwargs)

        if to or cc or bcc:
            for email in join_lists(to, cc, bcc):
                ToAddress.objects.create(
                    log_entry=new_entry,
                    email=email,
                )

        return new_entry

    @staticmethod
    def bulk_add_simple_entry(
        types,
        description,
        level,
        targets,
    ):
        new_entries = []
        for target in targets:
            new_entry = LogEntry()
            new_entry.types = types
            new_entry.description = description
            new_entry.level = level
            new_entry.target = target
            new_entries.append(new_entry)
        batch_size = 500
        return LogEntry.objects.bulk_create(new_entries, batch_size)


class ToAddress(models.Model):
    log_entry = models.ForeignKey(
        LogEntry,
        on_delete=models.CASCADE,
    )
    email = models.EmailField(max_length=300)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name_plural = 'to addresses'


class Version(models.Model):
    number = models.CharField(max_length=10)
    date = models.DateTimeField(default=timezone.now)
    rollback = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return 'Version {number}, upgraded {date}'.format(number=self.number, date=self.date)


class Plugin(models.Model):
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=10)
    date_installed = models.DateTimeField(auto_now_add=True)
    enabled = models.BooleanField(default=True)
    display_name = models.CharField(max_length=200, blank=True, null=True)
    press_wide = models.BooleanField(default=False)
    homepage_element = models.BooleanField(
        default=False,
        help_text='Enable if the plugin is a homepage element.'
    )

    def __str__(self):
        return u'[{0}] {1} - {2}'.format(self.name, self.version, self.enabled)

    def __repr__(self):
        return u'[{0}] {1} - {2}'.format(self.name, self.version, self.enabled)

    def best_name(self, slug=False):
        if self.display_name:
            name = self.display_name.lower()
        else:
            name = self.name.lower()

        if slug:
            return slugify(name)
        else:
            return name


setting_types = (
    ('rich-text', 'Rich Text'),
    ('mini-html', 'Mini HTML'),
    ('text', 'Plain Text'),
    ('char', 'Characters'),
    ('number', 'Number'),
    ('boolean', 'Boolean'),
    ('file', 'File'),
    ('select', 'Select'),
    ('json', 'JSON'),
)


class ImportCacheEntry(models.Model):
    url = models.TextField(max_length=800, blank=False, null=False)
    on_disk = models.TextField(max_length=800, blank=False, null=False)
    mime_type = models.CharField(max_length=200, null=True, blank=True)
    date_time = models.DateTimeField(default=timezone.now)

    @staticmethod
    def nuke():
        for cache in ImportCacheEntry.objects.all():
            cache.delete()

    def delete(self, *args, **kwargs):
        try:
            os.remove(self.on_disk)
        except FileNotFoundError:
            pass
        super().delete(*args, **kwargs)

    @staticmethod
    def fetch(url, up_auth_file='', up_base_url='', ojs_auth_file=''):
        try:
            cached = ImportCacheEntry.objects.get(url=url)

            if cached.date_time < timezone.now() - timezone.timedelta(minutes=30):
                cached.delete()
                if not settings.SILENT_IMPORT_CACHE:
                    print("[CACHE] Found old cached entry, expiring.")
                ImportCacheEntry.fetch(url, up_auth_file, up_base_url, ojs_auth_file)
            else:
                cached.date_time = timezone.now()
                cached.save()

            if not settings.SILENT_IMPORT_CACHE:
                print("[CACHE] Using cached version of {0}".format(url))

            with open(cached.on_disk, 'rb') as on_disk_file:
                return on_disk_file.read(), cached.mime_type

        except (ImportCacheEntry.DoesNotExist, FileNotFoundError):
            if not settings.SILENT_IMPORT_CACHE:
                print("[CACHE] Fetching remote version of {0}".format(url))

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/39.0.2171.95 Safari/537.36'}

            # disable SSL checking
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            # setup auth variables
            do_auth = False
            username = ''
            password = ''

            session = requests.Session()

            # first, check whether there's an auth file
            if up_auth_file != '':
                with open(up_auth_file, 'r', encoding="utf-8") as auth_in:
                    auth_dict = jason.loads(auth_in.read())
                    do_auth = True
                    username = auth_dict['username']
                    password = auth_dict['password']

            if do_auth:
                # load the login page
                auth_url = '{0}{1}'.format(up_base_url, '/login/')
                fetched = session.get(auth_url, headers=headers, stream=True, verify=False)
                csrf_token = get_input_value_by_name(fetched.content, 'csrfmiddlewaretoken')

                post_dict = {'username': username, 'password': password, 'login': 'login',
                             'csrfmiddlewaretoken': csrf_token}
                fetched = session.post('{0}{1}'.format(up_base_url, '/login/'), data=post_dict,
                                       headers={'Referer': auth_url,
                                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                                                              'Chrome/39.0.2171.95 Safari/537.36'
                                                })
                if not settings.SILENT_IMPORT_CACHE:
                    print("[CACHE] Sending auth")

            fetched = session.get(url, headers=headers, stream=True, verify=False)

            resp = bytes()

            for chunk in fetched.iter_content(chunk_size=512 * 1024):
                resp += chunk

            # set the filename to a unique UUID4 identifier with the passed file extension
            filename = '{0}'.format(uuid4())

            # set the path to save to be the sub-directory for the article
            path = os.path.join(settings.BASE_DIR, 'files', 'import_cache')

            # create the sub-folders as necessary
            if not os.path.exists(path):
                os.makedirs(path, 0o0775)

            with open(os.path.join(path, filename), 'wb') as f:
                f.write(resp)

            ImportCacheEntry.objects.update_or_create(
                url=url,
                defaults=dict(
                    mime_type=fetched.headers.get('content-type'),
                    on_disk=os.path.join(path, filename)
                ),
            )

            return resp, fetched.headers.get('content-type')

    def __str__(self):
        return self.url

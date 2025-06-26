__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json
import os
from uuid import uuid4
import requests
import tqdm

from requests.packages.urllib3.exceptions import InsecureRequestWarning

from django.utils import timezone
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from utils.logger import get_logger
from utils.shared import get_ip_address
from utils.importers.up import get_input_value_by_name


logger = get_logger(__name__)


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

EMAIL_RECIPIENT_FIELDS = [
    ('to', 'To'),
    ('cc', 'CC'),
    ('bcc', 'BCC'),
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
        """ Deprecated in 1.6 because of ambiguity with cc and bcc fields.
            Use addressee_emails instead.
        """
        return self.addressee_emails

    @property
    def addressees(self):
        return self.addressee_set.all()

    @property
    def addressee_emails(self):
        return set(addressee.email for addressee in self.addressee_set.all())

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

        for emails, field in [(to, 'to'), (cc, 'cc'), (bcc, 'bcc')]:
            if emails:
                for email in emails:
                    Addressee.objects.create(
                        log_entry=new_entry,
                        email=email,
                        field=field
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


class Addressee(models.Model):
    log_entry = models.ForeignKey(
        LogEntry,
        on_delete=models.CASCADE,
    )
    email = models.EmailField(max_length=300)
    field = models.CharField(
        max_length=3,
        blank=True,
        choices=EMAIL_RECIPIENT_FIELDS,
    )

    def __str__(self):
        return self.email


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
                    auth_dict = json.loads(auth_in.read())
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


class RORImport(models.Model):
    """
    A record of an import of ROR organization data into Janeway.
    """
    class RORImportStatus(models.TextChoices):
        IS_ONGOING = 'is_ongoing', _('Ongoing')
        IS_UNNECESSARY = 'is_unnecessary', _('Unnecessary')
        IS_SUCCESSFUL = 'is_successful', _('Successful')
        IS_FAILED = 'is_failed', _('Failed')

    started = models.DateTimeField(
        auto_now_add=True,
    )
    stopped = models.DateTimeField(
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=RORImportStatus.choices,
        default=RORImportStatus.IS_ONGOING,
    )
    records = models.JSONField(
        default=dict,
    )

    class Meta:
        get_latest_by = 'started'
        verbose_name = 'ROR import'
        verbose_name_plural = 'ROR imports'

    def __str__(self):
        return f'{self.get_status_display()} RORImport started { self.started }'

    @property
    def previous_import(self):
        try:
            return RORImport.objects.exclude(pk=self.pk).latest()
        except RORImport.DoesNotExist:
            return None

    @property
    def new_download_needed(self):
        if not self.previous_import:
            return True
        elif self.previous_import.status == self.RORImportStatus.IS_FAILED:
            return True
        elif not self.source_data_created or self.source_data_created > self.previous_import.started:
            return True
        else:
            return False

    @property
    def zip_path(self):
        temp_dir = os.path.join(settings.BASE_DIR, 'files', 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        try:
            file_id = self.records['hits']['hits'][0]['files'][-1]['id']
        except (KeyError, AttributeError) as error:
            self.fail(error)
            return ''
        zip_name = f'ror-download-{file_id}.zip'
        return os.path.join(temp_dir, zip_name)

    @property
    def download_link(self):
        try:
            return self.records['hits']['hits'][0]['files'][-1]['links']['self']
        except (KeyError, AttributeError) as error:
            self.fail(error)
            return ''

    @property
    def source_data_created(self):
        try:
            timestamp = self.records['hits']['hits'][0]['created']
            return timezone.datetime.fromisoformat(timestamp)
        except (KeyError, AttributeError) as error:
            self.fail(error)
            return None

    def fail(self, error):
        self.stopped = timezone.datetime.now()
        self.status = self.RORImportStatus.IS_FAILED
        self.save()
        logger.exception(error)
        logger.error(error)
        RORImportError.objects.create(ror_import=self, message=error)

    @property
    def is_ongoing(self):
        return self.status == self.RORImportStatus.IS_ONGOING

    def get_records(self):
        """
        Gets the manifest of available data and checks if it contains
        anything new. If the previous import failed or there is new data,
        the import is marked as ongoing.
        """
        logger.debug("Checking for availability of new ROR data")
        records_url = settings.ROR_RECORDS_FILE
        try:
            response = requests.get(records_url, timeout=settings.HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            self.records = response.json()
            self.save()
            if not self.new_download_needed:
                self.status = self.RORImportStatus.IS_ONGOING
                self.save()
        except requests.RequestException as error:
            self.fail(error)

    def delete_previous_download(self):
        if not self.previous_import:
            return
        try:
            os.unlink(self.previous_import.zip_path)
        except FileNotFoundError:
            logger.debug('Previous import had no zip file.')

    def download_data(self):
        """
        Downloads the current data dump from Zenodo.
        Then removes previous files to save space.
        """
        logger.debug("Downloading new ROR data")
        try:
            response = requests.get(
                self.download_link,
                timeout=settings.HTTP_TIMEOUT_SECONDS,
                stream=True,
            )
            response.raise_for_status()
            with open(self.zip_path, 'wb') as zip_ref:
                for chunk in response.iter_content(chunk_size=128):
                    zip_ref.write(chunk)
            if os.path.exists(self.zip_path):
                self.delete_previous_download()
        except requests.RequestException as error:
            self.fail(error)

    @staticmethod
    def filter_new_records(ror_data, existing_rors):
        """
        Finds records from the data dump that are new to Janeway,
        either because no earlier ROR import put them in Janeway,
        or because they have been recently added to the dump by ROR.
        """
        filtered_data = []
        for record in ror_data:
            ror_id = os.path.split(record.get('id', ''))[-1]
            if ror_id and ror_id not in existing_rors:
                filtered_data.append(record)
        logger.debug(f"{len(filtered_data)} new ROR records found")
        return filtered_data

    @staticmethod
    def filter_updated_records(ror_data, existing_rors):
        """
        Finds records from the data dump that Janeway already has,
        but which have been modified by ROR since the last Janeway import.
        """
        filtered_data = []
        for record in ror_data:
            ror_id = os.path.split(record.get('id', ''))[-1]
            last_modified = record.get("admin", {}).get("last_modified", {})
            timestamp = last_modified.get("date", "")
            if ror_id and timestamp and timestamp > existing_rors.get(ror_id, ''):
                filtered_data.append(record)
        logger.debug(f"{len(filtered_data)} updated ROR records found")
        return filtered_data


class RORImportError(models.Model):
    ror_import = models.ForeignKey(
        RORImport,
        on_delete=models.CASCADE,
    )
    message = models.TextField(
        blank=True,
    )

    class Meta:
        verbose_name = 'ROR import error'
        verbose_name_plural = 'ROR import errors'

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import re
import sys
import warnings

import requests
from bs4 import BeautifulSoup

from django.utils import timezone
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

from identifiers import logic
from utils import shared
from utils.logger import get_logger
from utils.function_cache import cache


logger = get_logger(__name__)

identifier_choices = (
    ('doi', 'DOI'),
    ('uri', 'URI Path'),
    ('pubid', 'Publisher ID'),
)

IDENTIFIER_TYPES = {
    'uri',
    'pubid',
    'id',
    'doi'
}

NON_DOI_IDENTIFIER_TYPES = IDENTIFIER_TYPES - {"doi"}

DOI_REGEX_PATTERN = '10.\d{4,9}/[-._;()/:A-Za-z0-9]+'
URL_DOI_REGEX_PATTERN = 'https://doi.org/10.\d{4,9}/[-._;()/:A-Za-z0-9]+'
PUB_ID_REGEX_PATTERN = '[\w-]+'
PUB_ID_RE = re.compile("^{}$".format(PUB_ID_REGEX_PATTERN))
DOI_RE = re.compile(DOI_REGEX_PATTERN)
URL_DOI_RE = re.compile(URL_DOI_REGEX_PATTERN)


class CrossrefDeposit(models.Model):
    """
    The booleans here have a priority order:
    1. If queued is True, other flags are meaningless.
    2. If success is False, then all other flags except queued should be disregarded as non-useful.
    3. If success is True but citation_success is False, then the deposit succeeded, but Crossref had trouble
    parsing some references for unknown reasons.

    The identifiers must all be for the same journal.
    """

    document = models.TextField(
        null=True,
        blank=True,
        help_text='The deposit document with rendered XML for the DOI batch.'
    )
    has_result = models.BooleanField(default=False)
    success = models.BooleanField(default=False)
    queued = models.BooleanField(default=False)
    citation_success = models.BooleanField(default=False)
    result_text = models.TextField(blank=True, null=False)
    file_name = models.CharField(blank=False, null=False, max_length=255)
    date_time = models.DateTimeField(default=timezone.now)
    polling_attempts = models.PositiveIntegerField(default=0)

    # Note: CrossrefDeposit.identifier is deprecated from version 1.4.2
    identifier = models.ForeignKey(
        "identifiers.Identifier",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('-date_time',)

    @property
    @cache(30)
    def parent_object(self):
        """
        Returns either a single journal or repository object.
        Raises an error if multiple journals or repositories are linked.
        """
        # Step 1: Check for linked journals
        journals = set(
            crossref_status.identifier.article.journal
            for crossref_status in self.crossrefstatus_set.all()
            if crossref_status.identifier.article
        )

        if len(journals) > 1:
            error = f"Identifiers from multiple journals passed to CrossrefDeposit: {journals}"
            logger.debug(error)
            return None
        elif len(journals) == 1:
            return journals.pop()

        # Step 2: If no journals found, check for linked repositories
        repositories = set(
            crossref_status.identifier.preprint_version.preprint.repository
            for crossref_status in self.crossrefstatus_set.all()
            if crossref_status.identifier.preprint_version
        )

        if len(repositories) > 1:
            error = f"Identifiers from multiple repositories passed to CrossrefDeposit: {repositories}"
            logger.debug(error)
            return None
        elif len(repositories) == 1:
            return repositories.pop()

        # Step 3: If no journals or repositories found, return None
        return None

    def journal(self):
        """
        Deprecated. Returns self.parent_object for backwards compatibility.
        """
        warnings.warn(
            "The 'journal' method is deprecated. Use 'parent_object' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.parent_object()

    def poll(self):
        self.polling_attempts += 1
        self.save()

        test_mode, username, password = logic.get_poll_settings(
            self.parent_object
        )

        if test_mode:
            test_var = 'test'
        else:
            test_var = 'doi'

        url = 'https://{3}.crossref.org/servlet/submissionDownload?usr={0}&pwd={1}&file_name={2}.xml&type=result'.format(username, password, self.file_name, test_var)

        try:
            response = requests.get(url, timeout=settings.HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            self.result_text = response.text
            self.has_result = ' status="unknown_submission"' not in self.result_text
            self.queued = 'status="queued"' in self.result_text or 'in_process' in self.result_text
            self.success = '<failure_count>0</failure_count>' in self.result_text and not 'status="queued"' in self.result_text
            self.citation_success = not ' status="error"' in self.result_text
            self.save()
            logger.debug(self)
            return f'Polled ({self.parent_object.name})', False
        except requests.RequestException as e:
            self.success = False
            self.has_result = True
            self.result_text = f'Error ({self.parent_object.name}): {e}'
            self.save()
            logger.error(self.result_text)
            logger.error(self)
            return f'Error ({self.parent_object.name})', True

    def get_record_diagnostic(self, doi):
        soup = BeautifulSoup(self.result_text, 'lxml-xml')
        record_diagnostics = soup.find_all('record_diagnostic')
        for record_diagnostic in record_diagnostics:
            if record_diagnostic.doi and record_diagnostic.doi.string:
                if doi in record_diagnostic.doi.string:
                    return str(record_diagnostic)

    def __str__(self):
        return ("[Deposit:{self.file_name}]"
            "[queued:{self.queued}]"
            "[success:{self.success}]"
            "[citation_success:{citation_success}]".format(
                self=self,
                #Citation success only to be considered for succesful deposits
                citation_success=self.citation_success if self.success else None,
            )
        )


class CrossrefStatus(models.Model):

    UNTRIED = 'untried'
    QUEUED = 'queued'
    REGISTERED = 'registered'
    REGISTERED_BUT_CITATION_PROBLEMS = 'registered_but_citation_problems'
    WARNING = 'warning'
    FAILED = 'failed'
    UNKNOWN = ''

    CROSSREF_STATUS_CHOICES = (
        (UNTRIED, 'Not yet registered'),
        (QUEUED, 'Queued at Crossref'),
        (REGISTERED, 'Registered'),
        (REGISTERED_BUT_CITATION_PROBLEMS, 'Registered (but some citations not correctly parsed)'),
        (WARNING, 'Registered with warning'),
        (FAILED, 'Registration failed'),
        (UNKNOWN, 'Unknown'),
    )

    identifier = models.OneToOneField(
        "identifiers.Identifier",
        on_delete=models.CASCADE,
    )
    deposits = models.ManyToManyField(
        "identifiers.CrossrefDeposit",
        blank=True,
    )
    message = models.CharField(
        blank=True,
        default='Unknown',
        max_length=255,
        help_text='A user-friendly message about the status of registration with Crossref.',
        choices=CROSSREF_STATUS_CHOICES,
    )

    def update(self):
        deposit = self.latest_deposit
        granular_status = self.get_granular_status()
        if not deposit:
            self.message = self.UNTRIED
        elif not deposit.document:
            self.message = self.UNTRIED
        elif deposit.queued:
            self.message = self.QUEUED
        elif deposit.success:
            if not deposit.citation_success:
                self.message = self.REGISTERED_BUT_CITATION_PROBLEMS
            elif granular_status:
                self.message = granular_status
        elif deposit.has_result:
            if granular_status:
                self.message = granular_status
            else:
                self.message = self.FAILED
        else:
            self.message = self.UNKNOWN

        # Prevent data not in choices from being saved
        if self.message not in dict(self.CROSSREF_STATUS_CHOICES):
            self.message = self.UNKNOWN

        self.save()

    def get_granular_status(self):
        doi = self.identifier.identifier
        try:
            record_diagnostic = self.latest_deposit.get_record_diagnostic(doi)
            if record_diagnostic:
                soup = BeautifulSoup(record_diagnostic, 'lxml-xml')
                tag = soup.record_diagnostic
                if tag['status'] == 'Success':
                    return self.REGISTERED
                elif tag['status'] == 'Warning':
                    return self.WARNING
                else:
                    return self.FAILED
        except AttributeError:
            return ''

    @property
    def latest_deposit(self):
        return self.deposits.first()

    def __str__(self):
        if self.latest_deposit:
            return f'{self.identifier} {self.message} ' \
                   f'{self.latest_deposit.date_time}'
        else:
            return self.message

    class Meta:
        verbose_name = 'Crossref status'
        verbose_name_plural = 'Crossref statuses'


class Identifier(models.Model):
    id_type = models.CharField(max_length=300, choices=identifier_choices)
    identifier = models.CharField(max_length=300)
    enabled = models.BooleanField(default=True)
    article = models.ForeignKey(
        "submission.Article",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    preprint_version = models.ForeignKey(
        "repository.PreprintVersion",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    review = models.ForeignKey(
        "review.ReviewAssignment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # TODO: Add validation to ensure only one FK is filled.

    def __str__(self):
        return u'[{0}]: {1}'.format(self.id_type.upper(), self.identifier)

    def register(self):
        if self.is_doi:
            return logic.register_crossref_doi(self)
        else:
            print("Not a DOI", file=sys.stderr)
            return "Identifier is not a DOI"

    def get_doi_url(self):
        if self.is_doi:
            return 'https://doi.org/{0}'.format(self.identifier)
        else:
            return 'This identifier is not a DOI.'

    @property
    def is_doi(self):
        if self.id_type == 'doi':
            return True
        return False

    @property
    def _object(self):
        return self.article or self.preprint_version or self.review or None


class BrokenDOI(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    identifier = models.ForeignKey(
        Identifier,
        on_delete=models.CASCADE,
    )
    checked = models.DateTimeField()
    resolves_to = models.URLField()
    expected_to_resolve_to = models.URLField()


# Signals
@receiver(post_save, sender=Identifier)
def reset_article_url_cache(sender, instance, created, **kwargs):
    shared.clear_cache()

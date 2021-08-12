__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import re
import sys
from django.utils import timezone

import requests
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from identifiers import logic
from utils import shared
from utils.logger import get_logger
from utils import setting_handler

from django.conf import settings

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
PUB_ID_REGEX_PATTERN = '[\w-]+'
PUB_ID_RE = re.compile("^{}$".format(PUB_ID_REGEX_PATTERN))
DOI_RE = re.compile(DOI_REGEX_PATTERN)


class CrossrefDeposit(models.Model):
    """
    The booleans here have a priority order:
    1. If queued is True, other flags are meaningless.
    2. If success is False, then all other flags except queued should be disregarded as non-useful.
    3. If success is True but citation_success is False, then the deposit succeeded, but Crossref had trouble
    parsing some references for unknown reasons.
    """

    identifier = models.ForeignKey("identifiers.Identifier", on_delete=models.CASCADE)
    has_result = models.BooleanField(default=False)
    success = models.BooleanField(default=False)
    queued = models.BooleanField(default=False)
    citation_success = models.BooleanField(default=False)
    result_text = models.TextField(blank=True, null=True)
    file_name = models.CharField(blank=False, null=False, max_length=255)
    date_time = models.DateTimeField(default=timezone.now)
    polling_attempts = models.PositiveIntegerField(default=0)

    def poll(self):
        self.polling_attempts += 1
        self.save()
        test_mode = setting_handler.get_setting('Identifiers',
                                                'crossref_test',
                                                self.identifier.article.journal).processed_value or settings.DEBUG
        username = setting_handler.get_setting('Identifiers', 'crossref_username',
                                               self.identifier.article.journal).processed_value
        password = setting_handler.get_setting('Identifiers', 'crossref_password',
                                               self.identifier.article.journal).processed_value

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
        except requests.RequestException as e:
            self.success = False
            self.has_result = True
            self.result_text = 'Error: {0}'.format(e)
            self.save()
            logger.error(self.result_text)
            logger.error(self)

    def __str__(self):
        return ("[Deposit:{self.identifier.identifier}:{self.file_name}]"
            "[queued:{self.queued}]"
            "[success:{self.success}]"
            "[citation_success:{citation_success}]".format(
                self=self,
                #Citation success only to be considered for succesful deposits
                citation_success=self.citation_success if self.success else None,
            )
        )


class Identifier(models.Model):
    id_type = models.CharField(max_length=300, choices=identifier_choices)
    identifier = models.CharField(max_length=300)
    enabled = models.BooleanField(default=True)
    article = models.ForeignKey("submission.Article", on_delete=models.CASCADE)

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
    def deposit(self):
        deposits = self.crossrefdeposit_set.all().order_by('-date_time')

        if deposits.count() > 0:
            return deposits[0]
        else:
            return None


class BrokenDOI(models.Model):
    article = models.ForeignKey('submission.Article')
    identifier = models.ForeignKey(Identifier)
    checked = models.DateTimeField()
    resolves_to = models.URLField()
    expected_to_resolve_to = models.URLField()


# Signals
@receiver(post_save, sender=Identifier)
def reset_article_url_cache(sender, instance, created, **kwargs):
    shared.clear_cache()

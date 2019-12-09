__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import re
import sys

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from submission import models as submission_models
from identifiers import logic
from utils import shared


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


class Identifier(models.Model):
    id_type = models.CharField(max_length=300, choices=identifier_choices)
    identifier = models.CharField(max_length=300)
    enabled = models.BooleanField(default=True)
    article = models.ForeignKey(submission_models.Article, on_delete=models.CASCADE)

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

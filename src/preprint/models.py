__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.db import models

from submission.models import Article

class Preprint(models.Model):
    article = models.ForeignKey(Article)
    doi = models.CharField(max_length=100)
    curent_version = models.IntegerField(default=1)

    def increase_version(self):
        self.curent_version = self.curent_version + 1
        self.save()

class PreprintVersion(models.Model):
    preprint = models.ForeignKey(Preprint)
    manuscript_files = models.ManyToManyField('core.File', null=True, blank=True, related_name='version_files')
    version = models.IntegerField(default=1)

class DOIPurchase(models.Model):
    preprint = models.ForeignKey(Preprint)
    transaction = models.CharField(max_length=100)

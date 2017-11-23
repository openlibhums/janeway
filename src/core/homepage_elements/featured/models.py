from django.db import models
from django.utils import timezone


class FeaturedArticle(models.Model):
    article = models.ForeignKey('submission.Article')
    journal = models.ForeignKey('journal.Journal')
    sequence = models.PositiveIntegerField(default=999)
    added = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey('core.Account')

    class Meta:
        ordering = ('sequence', 'added')

    def __str__(self):
        return "{0} - {1}".format(self.article.title, self.journal)

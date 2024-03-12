from django.db import models
from django.utils import timezone


class FeaturedArticle(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    journal = models.ForeignKey(
        'journal.Journal',
        on_delete=models.CASCADE,
    )
    sequence = models.PositiveIntegerField(default=999)
    added = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ('sequence', 'added')

    def __str__(self):
        return "{0} - {1}".format(self.article.title, self.journal)

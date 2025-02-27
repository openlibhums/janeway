from django.db import models
from django.utils import timezone

class CustomArticleLabel(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    label = models.CharField(max_length=999, blank=False, null=False)
    text = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    reminder_date = models.DateField(blank=True, null=True)
    creator = models.ForeignKey(
        'core.Account',
        default=None,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

class CustomArticleActionDate(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    next_date = models.DateField(default=timezone.now)

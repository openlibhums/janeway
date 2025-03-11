from django.db import models
from django.utils import timezone

class CustomArticleLabel(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        on_delete=models.CASCADE,
        related_name="custom_label",
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
    article = models.OneToOneField(
        'submission.Article',
        on_delete=models.CASCADE,
        related_name="custom_next_date",
        help_text=""
            "A custom date for the editorial team to know when to act next on"
            "an article."

    )
    next_date = models.DateField(default=timezone.now)

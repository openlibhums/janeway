from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class Thread(models.Model):
    article = models.ForeignKey(
        'submission.Article',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    preprint = models.ForeignKey(
        'repository.Preprint',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    owner = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
    )
    subject = models.CharField(
        max_length=300,
        help_text=_('Max. 300 characters.'),
    )
    started = models.DateTimeField(
        default=timezone.now,
    )
    last_updated = models.DateTimeField(
        default=timezone.now,
    )

    class Meta:
        ordering = ('-last_updated', 'pk')

    def __str__(self):
        return self.subject

    def object_title(self):
        if self.article:
            return self.article.title
        elif self.preprint:
            return self.preprint.title

    def object_string(self):
        if self.article:
            return 'article'
        elif self.preprint:
            return 'preprint'

    def object_id(self):
        if self.article:
            return self.article.pk
        else:
            return self.preprint.pk

    def posts(self):
        return self.post_set.all()

    def create_post(self, owner, body):
        self.last_updated = timezone.now()
        self.save()
        return self.post_set.create(
            owner=owner,
            body=body,
        )


class Post(models.Model):
    thread = models.ForeignKey(
        Thread,
        null=True,
        on_delete=models.SET_NULL,
    )
    owner = models.ForeignKey(
        'core.Account',
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
    )
    posted = models.DateTimeField(
        default=timezone.now,
    )
    body = models.TextField()
    read_by = models.ManyToManyField(
        'core.Account',
        blank=True,
    )

    class Meta:
        ordering = ('-posted', 'pk')

    def user_has_read(self, user):
        if user in self.read_by.all():
            return True
        return False

    def display_date(self):
        if self.posted.date() == timezone.now().date():
            return 'Today'
        else:
            return self.posted.date()

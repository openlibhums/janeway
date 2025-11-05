from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.timesince import timesince


class Thread(models.Model):
    article = models.ForeignKey(
        "submission.Article",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    preprint = models.ForeignKey(
        "repository.Preprint",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    owner = models.ForeignKey(
        "core.Account",
        null=True,
        on_delete=models.SET_NULL,
    )
    subject = models.CharField(
        max_length=300,
        help_text=_("Max. 300 characters."),
    )
    started = models.DateTimeField(
        default=timezone.now,
    )
    last_updated = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    participants = models.ManyToManyField(
        "core.Account",
        blank=True,
        related_name="accessible_threads",
        help_text=_("Users who are allowed to access this thread."),
    )

    class Meta:
        ordering = ("-last_updated", "pk")

    def __str__(self):
        return self.subject

    def clean(self):
        if self.article and self.preprint:
            raise ValidationError(
                _("A thread can only be attached to either an article or a preprint, not both."),
            )
        if not self.article and not self.preprint:
            raise ValidationError(
                _("A thread must be attached to either an article or a preprint."),
            )

    def object_title(self):
        if self.article:
            return self.article.safe_title
        elif self.preprint:
            return self.preprint.safe_title

    def object_string(self):
        if self.article:
            return "article"
        elif self.preprint:
            return "preprint"

    def object_id(self):
        if self.article:
            return self.article.pk
        if self.preprint:
            return self.preprint.pk
        return None

    def posts(self):
        return self.posts_related.all()

    def create_post(
        self,
        owner,
        body,
    ):
        post = self.posts_related.create(
            owner=owner,
            body=body,
        )

        # 🧭 Ensure the user is a participant if they're allowed to post
        if owner not in self.participants.all():
            self.participants.add(owner)

        # 🕒 Update the last_updated timestamp so threads sort correctly
        self.last_updated = timezone.now()
        self.save(update_fields=["last_updated"])

        return post

    def user_can_access(self, user):
        """
        Check whether a user can access this thread.

        Conditions:
          - User is the owner
          - User is in participants
          - User is editor of the journal
          - User is manager of the repository
        """
        if not user.is_authenticated:
            return False

        # Participant / owner
        if self.owner == user:
            return True
        if self.participants.filter(pk=user.pk).exists():
            return True

        # Editor or manager
        if self.article and self.article.journal:
            if user in self.article.journal.editors():
                return True

        if self.preprint and self.preprint.repository:
            if user in self.preprint.repository.managers.all():
                return True

        return False


class Post(models.Model):
    thread = models.ForeignKey(
        Thread,
        null=True,
        on_delete=models.CASCADE,
        related_name="posts_related",
    )
    owner = models.ForeignKey(
        "core.Account",
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    posted = models.DateTimeField(
        default=timezone.now,
    )
    body = models.TextField()
    read_by = models.ManyToManyField(
        "core.Account",
        blank=True,
    )

    class Meta:
        ordering = ("-posted", "pk")

    def __str__(self):
        owner_str = self.owner if self.owner else "Unknown"
        return f"Post by {owner_str} on {self.thread}"

    def save(
        self,
        *args,
        **kwargs,
    ):
        super().save(*args, **kwargs)
        if self.thread:
            self.thread.last_updated = timezone.now()
            self.thread.save(
                update_fields=["last_updated"],
            )

    def user_has_read(
        self,
        user,
    ):
        return self.read_by.filter(
            pk=user.pk,
        ).exists()

    def display_date(self):
        now = timezone.now()
        if self.posted.date() == now.date():
            return "Today"
        return f"{timesince(self.posted, now)} ago"

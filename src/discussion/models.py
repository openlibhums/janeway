import bleach
import markdown as markdown_lib

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.timesince import timesince

MARKDOWN_ALLOWED_TAGS = [
    "p", "br", "strong", "em", "a", "code", "pre",
    "ul", "ol", "li", "blockquote",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "img",
    "del", "sub", "sup",
]

MARKDOWN_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt"],
    "code": ["class"],
}


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

    def user_posts(self):
        return self.posts_related.filter(is_system_message=False)

    def create_system_post(self, actor, body):
        """Create a system message in this thread."""
        return self.posts_related.create(
            owner=actor,
            body=body,
            is_system_message=True,
        )

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
            self.posts_related.create(
                owner=owner,
                body=f"{owner.full_name()} joined the discussion",
                is_system_message=True,
            )

        return post

    def unread_count_for(self, user):
        return self.user_posts().exclude(read_by=user).count()

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
    is_system_message = models.BooleanField(
        default=False,
        help_text=_("System-generated message, e.g. title change or participant added."),
    )
    file = models.ForeignKey(
        "core.File",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Optional file attachment."),
    )
    read_by = models.ManyToManyField(
        "core.Account",
        blank=True,
    )
    edited = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp of the last edit, if any."),
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
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.thread:
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

    @property
    def body_html(self):
        """Return the post body as sanitized HTML, converting markdown."""
        raw_html = markdown_lib.markdown(
            self.body,
            extensions=["nl2br", "fenced_code", "sane_lists"],
        )
        return mark_safe(
            bleach.clean(
                raw_html,
                tags=MARKDOWN_ALLOWED_TAGS,
                attributes=MARKDOWN_ALLOWED_ATTRIBUTES,
                strip=True,
            )
        )

    def display_date(self):
        now = timezone.now()
        if self.posted.date() == now.date():
            return "Today"
        return f"{timesince(self.posted, now)} ago"

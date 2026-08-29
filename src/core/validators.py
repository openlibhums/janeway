import logging
import mimetypes
import os.path
import random
import string

from django.core.exceptions import ValidationError
from django.template import Template
from django.template.exceptions import TemplateSyntaxError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class FileTypeValidator(object):
    """Validates file against given lists of extensions and mimetypes
    :param extensions: iterable object (ideally a set)
    :param mimetypes: iterable object (ideally a set)
    """

    error_messages = {
        "ext": _(
            "Extension {extension} is not allowed. "
            "Allowed extensions are: {validator.extensions}"
        ),
        "mime": _(
            "MIME type {mimetype} is not valid. Valid types are: {validator.mimetypes}"
        ),
    }

    def __init__(self, extensions=None, mimetypes=None):
        self.extensions = extensions
        self.mimetypes = mimetypes

    def __call__(self, file_):
        if self.extensions:
            self.validate_extension(file_.name)
        if self.mimetypes:
            self.validate_mimetype(file_.name)

    def validate_extension(self, file_name):
        _, extension = os.path.splitext(file_name)
        if extension not in self.extensions:
            message = self.error_messages["ext"].format(
                extension=extension,
                validator=self,
            )

            raise ValidationError(message, code="invalid_extension")

    def validate_mimetype(self, file_name):
        mimetype, _ = mimetypes.guess_type(file_name)
        if mimetype not in self.mimetypes:
            message = self.error_messages["mime"].format(
                mimetype=mimetype,
                validator=self,
            )

            raise ValidationError(message, code="invalidi_mimetype")


def validate_email_setting(value):
    try:
        template = Template(value)
    except TemplateSyntaxError as error:
        raise ValidationError(str(error))


# Journal.code and Repository.short_name both occupy the single path segment
# which may clash with press-level routes.
RESERVED_URL_PREFIXES = frozenset(
    {
        "__debug__",
        "__reload__",
        "404",
        "500",
        "admin",
        "alt-text",
        "api-auth",
        "api",
        "article",
        "cms",
        "conferences",
        "control_user",
        "copyediting",
        "cron",
        "dashboard",
        "discussion",
        "doi_manager",
        "download",
        "edit",
        "feed",
        "homepage",
        "i18n",
        "identifiers",
        "install",
        "issue",
        "journals",
        "jsi18n",
        "kanban",
        "login",
        "logout",
        "manager",
        "media",
        "metrics",
        "news",
        "oidc",
        "permission",
        "plugins",
        "press",
        "preview",
        "production",
        "profile",
        "proofing",
        "register",
        "reports",
        "repository",
        "reset",
        "review",
        "robots.txt",
        "rss",
        "set-timezone",
        "site",
        "sitemap.xml",
        "subject",
        "submit",
        "summernote",
        "transform",
        "typesetting",
        "utils",
        "workflow",
    }
)


def is_reserved(value):
    return bool(value) and value.strip().lower() in RESERVED_URL_PREFIXES


def validate_code(value, kind, max_length, exclude_pk=None):
    # No Press configured at all (a standalone journal install) — reserved
    # words and cross-model collisions both exist to protect a shared
    # press-level URL namespace, so with no press there's nothing to check.
    from press.models import Press

    if not Press.objects.exists():
        return

    journal_codes, repository_codes = _existing_codes(kind, exclude_pk)
    taken = journal_codes | repository_codes

    if is_reserved(value):
        raise ValidationError(
            _code_error_message(
                "reserved",
                value,
                kind,
                _find_available_code(value, kind, max_length, taken),
            ),
            code="reserved",
        )

    held_by = _held_by(value, journal_codes, repository_codes)
    if held_by:
        raise ValidationError(
            _code_error_message(
                held_by,
                value,
                kind,
                _find_available_code(value, kind, max_length, taken),
            ),
            code=held_by,
        )


def _held_by(value, journal_codes, repository_codes):
    """Returns "journal" or "repository" — whichever set already holds
    `value` — or None if it's in neither.
    """
    if value in journal_codes:
        return "journal"
    if value in repository_codes:
        return "repository"
    return None


def _existing_codes(kind, exclude_pk):
    """(journal_codes, repository_codes) — every Journal.code and every
    Repository.short_name currently in use, as two sets. Fetched once per
    validate_code() call and reused.
    """
    # Deferred imports: core.validators must not import journal/repository
    # models at module load time (those apps import core.validators).
    from journal.models import Journal
    from repository.models import Repository

    journal_qs = Journal.objects.all()
    repository_qs = Repository.objects.all()
    if exclude_pk:
        if kind == "journal":
            journal_qs = journal_qs.exclude(pk=exclude_pk)
        else:
            repository_qs = repository_qs.exclude(pk=exclude_pk)

    return (
        set(journal_qs.values_list("code", flat=True)),
        set(repository_qs.values_list("short_name", flat=True)),
    )


def _find_available_code(value, kind, max_length, taken):
    """
    "journal" or "repository" — determines the prefix/suffix letter ("j"/"r").
    Returns None (never raises) if no available candidate can be found (highly unlikely edgecase)
    """
    letter = "j" if kind == "journal" else "r"
    base = (value or "").strip().lower()

    def available(candidate):
        candidate = candidate[:max_length]
        if not candidate or is_reserved(candidate) or candidate in taken:
            return None
        return candidate

    for candidate in (
        (letter + base)[:max_length],
        (base + letter)[:max_length],
    ):
        result = available(candidate)
        if result:
            return result

    # Fallback: a short, unrelated code
    for _attempt in range(50):
        candidate = "".join(random.choices(string.ascii_lowercase, k=4))
        result = available(candidate)
        if result:
            return result

    # 26**4 possibilities ~ practically unreachable. Log it for diagnosis, but the user
    # never sees a failed-suggestion state; callers just omit the clause.
    logger.warning(
        "Could not generate an available %s code suggestion for %r.",
        kind,
        value,
    )
    return None


def _code_error_message(error_type, value, kind, suggestion):
    """
    Builds the user-facing message for a validate_code() failure.
    `error_type`/`suggestion` are validate_code()'s own findings; `kind` is
    the caller's own kind, needed only to phrase "another repository" (the
    value's own model held it) vs "a repository" (the other model did).
    """
    if error_type == "reserved":
        if suggestion:
            return _(
                "'%(value)s' can't be used because it conflicts with a "
                "built-in Janeway system page (a code of '%(value)s' would "
                "collide with the site's /%(value)s/ area). Try "
                "'%(suggestion)s' instead, or choose your own alternative."
            ) % {"value": value, "suggestion": suggestion}
        return _(
            "'%(value)s' can't be used because it conflicts with a built-in "
            "Janeway system page (a code of '%(value)s' would collide with "
            "the site's /%(value)s/ area). Please choose a different code."
        ) % {"value": value}

    taken_by = ("another %s" if error_type == kind else "a %s") % error_type
    if suggestion:
        return _(
            "'%(value)s' is already in use by %(taken_by)s. Try "
            "'%(suggestion)s' instead, or choose your own alternative."
        ) % {"value": value, "taken_by": taken_by, "suggestion": suggestion}
    return _(
        "'%(value)s' is already in use by %(taken_by)s. Please choose a different code."
    ) % {"value": value, "taken_by": taken_by}

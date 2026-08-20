import mimetypes
import os.path

from django.core.exceptions import ValidationError
from django.template import Template
from django.template.exceptions import TemplateSyntaxError
from django.utils.translation import gettext_lazy as _


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
        "404",
        "500",
        "admin",
        "article",
        "cms",
        "conferences",
        "issue",
        "journals",
        "login",
        "logout",
        "manager",
        "news",
        "plugins",
        "press",
        "register",
        "rss",
        "site",
        "sitemap.xml",
    }
)

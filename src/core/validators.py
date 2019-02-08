import mimetypes
import os.path

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class FileTypeValidator(object):
    """ Validates file against given lists of extensions and mimetypes
    :param extensions: iterable object (ideally a set)
    :param mimetypes: iterable object (ideally a set)
    """
    error_messages = {
        "ext": _("Extension {extension} is not allowed. "
                 "Allowed extensions are: {validator.extensions}"),
        "mime": _("MIME type {mimetype} is not valid. "
                  "Valid types are: {validator.mimetypes}"),
    }

    def __init__(self, extensions=None, mimetypes=None):
        self.extensions = extensions or []
        self.mimetypes = mimetypes or []

    def __call__(self, file_):
        self.validate_extension(file_.name)
        self.validate_mimetype(file_.name)

    def validate_extension(self, file_name):
        _, extension = os.path.splitext(file_name)
        if extension not in self.extensions:
            message = self.error_messages["ext"].format(
                extension=extension,
                validator=self,
            )

            raise ValidationError(message, code="invalid")

    def validate_mimetype(self, file_name):
        mimetype, _ = mimetypes.guess_type(file_name)
        if mimetype not in self.mimetypes:
            message = self.error_messages["mime"].format(
                mimetype=mimetype,
                validator=self,
            )

            raise ValidationError(message, code="invalid")

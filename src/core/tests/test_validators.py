from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.core.exceptions import ValidationError
from core import models, validators

class TestValidators(TestCase):

    def test_valid_file(self):
        valid_extensions = {".gz"}
        valid_mimetypes = {"application/x-tar"}
        validator = validators.FileTypeValidator(
            extensions=valid_extensions,
            mimetypes=valid_mimetypes,
        )
        file_ = SimpleUploadedFile("test.tar.gz", content=None)
        try:
            validator(file_)
        except ValidationError as e:
            error = e
        else:
            error = None

        self.assertIsNone(error)

    def test_invalid_file_extension(self):
        valid_extensions = {".gz"}
        valid_mimetypes = {"application/x-tar"}
        validator = validators.FileTypeValidator(extensions=valid_extensions)
        file_ = SimpleUploadedFile("test.tar.bz2", bytes())

        with self.assertRaises(ValidationError):
            validator(file_)


    def test_invalid_mime_type(self):
        valid_extensions = {".gz"}
        valid_mimetypes = {"application/x-tar"}
        validator = validators.FileTypeValidator(mimetypes=valid_mimetypes)
        file_ = SimpleUploadedFile("test.gz", bytes())


        with self.assertRaises(ValidationError):
            validator(file_)

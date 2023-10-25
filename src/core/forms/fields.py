from django import forms
from django.core.exceptions import ValidationError

from core.forms.widgets import TagitWidget


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class TagitField(forms.CharField):
    widget = TagitWidget

    def to_python(self, value):
        if value:
            try:
                return tuple(item for item in value.split(","))
            except (AttributeError, ValueError):
                raise ValidationError(
                    "%s is not a valid value for %s"
                    "" % (value, self.label)
                )
        return tuple()

from django import forms
from django.core.exceptions import ValidationError

from core.forms.widgets import TagitWidget


class TagitField(forms.CharField):
    widget = TagitWidget

    def to_python(self, value):
        if value:
            try:
                return [item for item in value.split(",")]
            except (AttributeError, ValueError):
                raise ValidationError(
                    "%s is not a valid value for %s"
                    "" % (value, self.label)
                )
        return []

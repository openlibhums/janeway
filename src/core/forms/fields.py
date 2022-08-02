
from django import forms

from core.forms.widgets import TagitWidget


class TagitField(forms.CharField):
    widget = TagitWidget

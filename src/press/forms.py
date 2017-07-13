__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms
from django.contrib.contenttypes.models import ContentType

from press import models
from journal import models as journal_models
from core import models as core_models


class PressForm(forms.ModelForm):

    class Meta:
        model = models.Press
        exclude = ('domain', 'thumbnail_image',)
        widgets = {'featured_journals': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super(PressForm, self).__init__(*args, **kwargs)
        press = models.Press.objects.all()[0]
        content_type = ContentType.objects.get_for_model(press)

        self.fields['featured_journals'].queryset = journal_models.Journal.objects.filter(hide_from_press=False)
        self.fields['carousel_news_items'].queryset = core_models.NewsItem.objects.filter(
            content_type=content_type,
            object_id=press.pk
        )

from django import forms

from django_summernote.widgets import SummernoteWidget

from comms import models


class NewsItemForm(forms.ModelForm):

    image_file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super(NewsItemForm, self).__init__(*args, **kwargs)
        self.fields['body'].widget = SummernoteWidget()

    class Meta:
        model = models.NewsItem
        exclude = ('content_type', 'object_id', 'posted', 'posted_by', 'large_image_file')
from django import forms

from django_summernote.widgets import SummernoteWidget

from comms import models


class NewsItemForm(forms.ModelForm):


    image_file = forms.FileField(required=False)
    tags = forms.CharField(required=False)

    def save(self, commit=True):
        news_item = super(NewsItemForm, self).save()
        posted_tags = self.cleaned_data['tags'].split(',')
        news_item.set_tags(posted_tags=posted_tags)
        news_item.save()

        return news_item

    class Meta:
        model = models.NewsItem
        exclude = ('content_type', 'object_id', 'posted', 'posted_by', 'large_image_file', 'tags')

from django import forms
from django.utils import timezone

from comms import models
from utils.forms import HTMLDateInput, JanewayTranslationModelForm


class NewsItemForm(JanewayTranslationModelForm):
    image_file = forms.FileField(required=False)
    tags = forms.CharField(required=False)

    class Meta:
        model = models.NewsItem
        exclude = (
            "content_type",
            "object_id",
            "posted",
            "posted_by",
            "large_image_file",
            "tags",
        )
        widgets = {
            "start_display": HTMLDateInput,
            "end_display": HTMLDateInput,
        }

    def __init__(self, *args, **kwargs):
        self.content_type = kwargs.pop("content_type", None)
        self.object_id = kwargs.pop("object_id", None)
        self.posted_by = kwargs.pop("posted_by", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        news_item = super().save(commit=False)

        # Set the attributes only on first save
        if not news_item.pk:
            news_item.content_type = self.content_type
            news_item.object_id = self.object_id
            news_item.posted_by = self.posted_by
            news_item.posted = timezone.now()

        if commit:
            news_item.save()
            posted_tags = (
                self.cleaned_data["tags"].split(",")
                if self.cleaned_data["tags"]
                else []
            )
            news_item.set_tags(posted_tags=posted_tags)

        return news_item

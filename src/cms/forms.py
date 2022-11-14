__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django import forms

from django_summernote.widgets import SummernoteWidget

from cms import models
from core import models as core_models
from utils.forms import JanewayTranslationModelForm


class PageForm(JanewayTranslationModelForm):

    class Meta:
        model = models.Page
        fields = ('display_name', 'name', 'content')
        exclude = ('journal', 'is_markdown', 'content_type', 'object_id')

    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)

        self.fields['content'].widget = SummernoteWidget()


class NavForm(JanewayTranslationModelForm):

    class Meta:
        model = models.NavigationItem
        fields = ('link_name', 'link', 'is_external', 'sequence', 'has_sub_nav', 'top_level_nav')
        exclude = ('page', 'content_type', 'object_id')

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(NavForm, self).__init__(*args, **kwargs)
        top_level_nav_items = models.NavigationItem.objects.filter(
            content_type=request.model_content_type,
            object_id=request.site_type.pk,
            has_sub_nav=True,
        )

        if self.instance:
            top_level_nav_items = top_level_nav_items.exclude(pk=self.instance.pk)

        self.fields['top_level_nav'].queryset = top_level_nav_items

    def clean_top_level_nav(self):
        top_level_nav = self.cleaned_data.get('top_level_nav')
        if (top_level_nav and self.instance) and (top_level_nav.pk == self.instance.pk):
            self.add_error(
                'top_level_nav',
                'You cannot assign a Nav Item to itself as Top Level Nav item.',
            )

        return top_level_nav


class SubmissionItemForm(JanewayTranslationModelForm):

    class Meta:
        model = models.SubmissionItem
        fields = ('title', 'text', 'order', 'existing_setting')
        exclude = ('journal',)
        widgets = {
            'text': SummernoteWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal')
        super(SubmissionItemForm, self).__init__(*args, **kwargs)

        self.fields['existing_setting'].queryset = core_models.Setting.objects.filter(
            types='rich-text',
        )

    def save(self, commit=True):
        item = super(SubmissionItemForm, self).save(commit=False)
        item.journal = self.journal

        if commit:
            item.save()

        return item


class MediaFileForm(forms.ModelForm):
    class Meta:
        model = models.MediaFile
        fields = (
            'label',
            'file',
        )

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal', None)
        super(MediaFileForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        media_file = super(MediaFileForm, self).save(commit=False)
        media_file.journal = self.journal

        if commit:
            media_file.save()

        return media_file

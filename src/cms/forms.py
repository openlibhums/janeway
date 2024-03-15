__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from cms import logic, models
from core import models as core_models
from utils.forms import JanewayTranslationModelForm


class PageForm(JanewayTranslationModelForm):

    class Meta:
        model = models.Page
        exclude = ('is_markdown', 'content_type', 'object_id')

    def __init__(self, *args, **kwargs):
        # Set the press and journal from the request, if request is passed
        self.request = kwargs.pop('request', None)
        self.journal = self.request.journal if self.request else None
        self.press = self.request.press if self.request else None

        super(PageForm, self).__init__(*args, **kwargs)

        if self.instance:
            # Overwrite the journal and press if defined on the instance
            journal_type = ContentType.objects.get(app_label="journal", model="journal")
            if self.instance.content_type == journal_type:
                self.journal = journal_type.get_object_for_this_type(pk=self.instance.object_id)
            press_type = ContentType.objects.get(app_label="press", model="press")
            if self.instance.content_type == press_type:
                self.press = press_type.get_object_for_this_type(pk=self.instance.object_id)

        custom_templates = logic.get_custom_templates(self.journal, self.press)

        if custom_templates:
            self.fields['template'].widget = forms.Select(
                choices=custom_templates
            )
        else:
            self.fields.pop('template')


class NavForm(JanewayTranslationModelForm):

    class Meta:
        model = models.NavigationItem
        fields = (
            'link_name',
            'link',
            'is_external',
            'sequence',
            'has_sub_nav',
            'top_level_nav',
            'for_footer',
            'extend_to_journals',
        )
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

        if request.journal:
            # Remove this until it can be implemented at the journal level
            self.fields.pop('for_footer')
            # Remove this at the journal level
            self.fields.pop('extend_to_journals')


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

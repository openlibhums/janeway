__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms

from cms import models


class PageForm(forms.ModelForm):

    class Meta:
        model = models.Page
        exclude = ('journal', 'is_markdown', 'content_type', 'object_id')


class NavForm(forms.ModelForm):

    class Meta:
        model = models.NavigationItem
        exclude = ('page', 'content_type', 'object_id')

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(NavForm, self).__init__(*args, **kwargs)

        self.fields['top_level_nav'].queryset = models.NavigationItem.objects.filter(
            content_type=request.content_type,
            has_sub_nav=True,
        )

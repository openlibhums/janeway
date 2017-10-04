from django import forms
from django.utils.translation import ugettext_lazy as _

from submission import models

class PreprintInfo(forms.ModelForm):
    keywords = forms.CharField(required=False)

    class Meta:
        model = models.Article
        fields = ('title', 'subtitle', 'abstract', 'language', 'license', 'comments_editor')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Title')}),
            'subtitle': forms.TextInput(attrs={'placeholder': _('Subtitle')}),
            'abstract': forms.Textarea(
                attrs={'placeholder': _('Enter your article\'s abstract here')}),
        }

    def __init__(self, *args, **kwargs):
        super(PreprintInfo, self).__init__(*args, **kwargs)

        self.fields['license'].queryset = models.Licence.objects.filter(available_for_submission=True)
        self.fields['license'].required = True


    def save(self, commit=True, request=None):
        article = super(PreprintInfo, self).save()

        posted_keywords = self.cleaned_data['keywords'].split(',')
        for keyword in posted_keywords:
            new_keyword, c = models.Keyword.objects.get_or_create(word=keyword)
            article.keywords.add(new_keyword)

        for keyword in article.keywords.all():
            if keyword.word not in posted_keywords:
                article.keywords.remove(keyword)

        return article
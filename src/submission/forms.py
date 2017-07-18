__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django import forms
from django.utils.translation import ugettext_lazy as _

from submission import models
from core import models as core_models
from identifiers import models as ident_models


class PublisherNoteForm(forms.ModelForm):

    class Meta:
        model = models.PublisherNote
        fields = ('text',)


class ArticleStart(forms.ModelForm):

    class Meta:
        model = models.Article
        fields = ('publication_fees', 'submission_requirements', 'copyright_notice', 'comments_editor',
                  'competing_interests')

    def __init__(self, *args, **kwargs):
        ci = kwargs.pop('ci', False)
        super(ArticleStart, self).__init__(*args, **kwargs)

        if not ci:
            self.fields['competing_interests'].required = False


class ArticleInfo(forms.ModelForm):
    keywords = forms.CharField(required=False)

    class Meta:
        model = models.Article
        fields = ('title', 'subtitle', 'abstract', 'language', 'section', 'license', 'primary_issue',
                  'page_numbers', 'is_remote', 'remote_url')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Title')}),
            'subtitle': forms.TextInput(attrs={'placeholder': _('Subtitle')}),
            'abstract': forms.Textarea(
                attrs={'placeholder': _('Enter your article\'s abstract here')}),
        }

    def __init__(self, *args, **kwargs):
        super(ArticleInfo, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            article = kwargs['instance']
            self.fields['section'].queryset = models.Section.objects.language().fallbacks('en').filter(
                journal=article.journal, public_submissions=True)
            self.fields['license'].queryset = article.journal.licence_set.all()
            self.fields['section'].required = True
            self.fields['license'].required = True
            self.fields['primary_issue'].queryset = article.journal.issues()

    def save(self, commit=True):
        article = super(ArticleInfo, self).save(commit=False)

        posted_keywords = self.cleaned_data['keywords'].split(',')
        for keyword in posted_keywords:
            new_keyword, c = models.Keyword.objects.get_or_create(word=keyword)
            article.keywords.add(new_keyword)

        for keyword in article.keywords.all():
            if keyword.word not in posted_keywords:
                article.keywords.remove(keyword)

        if commit:
            article.save()

        return article


class AuthorForm(forms.ModelForm):

    class Meta:
        model = core_models.Account
        exclude = (
            'date_joined',
            'activation_code'
            'date_confirmed'
            'confirmation_code'
            'reset_code'
            'reset_code_validated'
            'roles'
            'interest'
            'is_active'
            'is_staff'
            'is_admin'
            'password',
            'username',
            'roles',

        )

        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'middle_name': forms.TextInput(attrs={'placeholder': 'Middle name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'biography': forms.Textarea(
                attrs={'placeholder': 'Enter biography here'}),
            'institution': forms.TextInput(attrs={'placeholder': 'Institution'}),
            'department': forms.TextInput(attrs={'placeholder': 'Department'}),
            'twitter': forms.TextInput(attrs={'placeholder': 'Twitter handle'}),
            'linkedin': forms.TextInput(attrs={'placeholder': 'LinkedIn profile'}),
            'impactstory': forms.TextInput(attrs={'placeholder': 'ImpactStory profile'}),
            'orcid': forms.TextInput(attrs={'placeholder': 'ORCID ID'}),
            'email': forms.TextInput(attrs={'placeholder': 'Email address'}),

        }

    def __init__(self, *args, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)
        self.fields['password'].required = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class FileDetails(forms.ModelForm):

    class Meta:
        model = core_models.File
        fields = (
            'label',
            'description',
        )

    def __init__(self, *args, **kwargs):
        super(FileDetails, self).__init__(*args, **kwargs)
        self.fields['label'].required = True


class EditFrozenAuthor(forms.ModelForm):

    class Meta:
        model = models.FrozenAuthor
        fields = (
            'first_name',
            'middle_name',
            'last_name',
            'institution',
            'department',
            'country',
        )


class IdentifierForm(forms.ModelForm):

    class Meta:
        model = ident_models.Identifier
        fields = (
            'id_type',
            'identifier',
            'enabled',
        )

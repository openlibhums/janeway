__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.validators import validate_email, ValidationError

from simplemathcaptcha.fields import MathCaptchaField
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget
from django_summernote.widgets import SummernoteWidget
from hcaptcha.fields import hCaptchaField

from core import models as core_models
from journal import models as journal_models, logic
from utils.forms import CaptchaForm, LeftBooleanField

SEARCH_SORT_OPTIONS = [
        # Translators: Search order options
        ('relevance', _('Relevance')),
        ('title', _('Titles A-Z')),
        ('-title', _('Titles Z-A')),
        ('-date_published', _('Newest')),
        ('date_published', _('Oldest')),
      ]


class JournalForm(forms.ModelForm):

    class Meta:
        model = journal_models.Journal
        fields = ('code', 'domain')
        help_texts = {
            'domain': 'Using a custom domain requires configuring DNS. '
                'The journal will always be available under the /code path',
        }


class ContactForm(forms.ModelForm, CaptchaForm):

    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', None)
        contacts = kwargs.pop('contacts', None)
        super(ContactForm, self).__init__(*args, **kwargs)

        if subject:
            self.fields['subject'].initial = subject

        if contacts:
            contact_choices = []
            for contact in contacts:
                contact_choices.append([contact.email, '{name}, {role}'.format(name=contact.name, role=contact.role)])
            self.fields['recipient'].widget = forms.Select(choices=contact_choices)

    class Meta:
        model = core_models.Contact
        fields = ('recipient', 'sender', 'subject', 'body')


class ResendEmailForm(forms.Form):
    to = forms.CharField(max_length=1000, help_text='Seperate email addresses with ;')
    subject = forms.CharField(max_length=1000)
    body = forms.CharField(widget=SummernoteWidget)

    def __init__(self, *args, **kwargs):
        log_entry = kwargs.pop('log_entry')
        super(ResendEmailForm, self).__init__(*args, **kwargs)

        self.fields['to'].initial = ';'.join(log_entry.to)
        self.fields['subject'].initial = log_entry.subject
        self.fields['body'].initial = mark_safe(log_entry.description)


class EmailForm(forms.Form):
    cc = forms.CharField(
        required=False,
        max_length=1000,
        help_text='Separate email addresses with ;',
    )
    subject = forms.CharField(max_length=1000)
    body = forms.CharField(widget=SummernoteWidget)

    def clean_cc(self):
        cc = self.cleaned_data['cc']
        if not cc or cc == '':
            return []

        cc_list = [x.strip() for x in cc.split(';') if x]
        for address in cc_list:
            try:
                validate_email(address)
            except ValidationError:
                self.add_error('cc', 'Invalid email address ({}).'.format(address))

        return cc_list


class SearchForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.ENABLE_FULL_TEXT_SEARCH:
            self.fields.pop('full_text', None)

    article_search = forms.CharField(label=_('Search term'), min_length=3, max_length=100, required=False)
    title = LeftBooleanField(initial=True, label=_('Search Titles'), required=False)
    abstract = LeftBooleanField(initial=True, label=_('Search Abstract'), required=False)
    authors = LeftBooleanField(initial=True, label=_('Search Authors'), required=False)
    keywords = LeftBooleanField(label=_("Search Keywords"), required=False)
    full_text = LeftBooleanField(initial=True, label=_("Search Full Text"), required=False)
    orcid = LeftBooleanField(label=_("Search ORCIDs"), required=False)
    sort = forms.ChoiceField(label=_('Sort results by'), widget=forms.Select, choices=SEARCH_SORT_OPTIONS)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.ENABLE_FULL_TEXT_SEARCH:
            self.fields["sort"].choices = SEARCH_SORT_OPTIONS[1:]

    def get_search_filters(self):
        """ Generates a dictionary of search_filters from a search form"""
        return {
            "full_text": self.cleaned_data["full_text"],
            "title": self.cleaned_data["title"],
            "authors": self.cleaned_data["authors"],
            "abstract": self.cleaned_data["abstract"],
            "keywords": self.cleaned_data["keywords"],
            "orcid": self.cleaned_data["orcid"],
        }


class IssueDisplayForm(forms.ModelForm):
    class Meta:
        model = journal_models.Journal
        fields = (
            'display_issue_volume',
            'display_issue_number',
            'display_issue_year',
            'display_issue_title',
            'display_article_number',
            'display_article_page_numbers',
        )

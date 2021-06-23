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

from core import models as core_models
from journal import models as journal_models, logic

SEARCH_SORT_OPTIONS = [
        ('title', 'Titles A-Z'),
        ('-title', 'Titles Z-A'),
        ('-date_published', 'Newest'),
        ('date_published', 'Oldest'),
      ]


class JournalForm(forms.ModelForm):

    class Meta:
        model = journal_models.Journal
        fields = ('code', 'domain')

    def __init__(self, *args, **kwargs):
        super(JournalForm, self).__init__(*args, **kwargs)
        if settings.URL_CONFIG == 'path':
            self.fields.pop('domain')

    def save(self, commit=True, request=None):
        journal = super(JournalForm, self).save(commit=False)

        if settings.URL_CONFIG == 'path':
            journal.domain = '{press_domain}/{path}'.format(press_domain=request.press.domain, path=journal.code)

        if commit:
            journal.save()

        return journal


class ContactForm(forms.ModelForm):

    if settings.CAPTCHA_TYPE == 'simple_math':
        question_template = _('What is %(num1)i %(operator)s %(num2)i? ')
        are_you_a_robot = MathCaptchaField(label=_('Answer this question: '))
    elif settings.CAPTCHA_TYPE == 'recaptcha':
        are_you_a_robot = ReCaptchaField(widget=ReCaptchaWidget())
    else:
        are_you_a_robot = forms.CharField(widget=forms.HiddenInput(), required=False)

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
    article_search = forms.CharField(label='search term', min_length=3, max_length=100, required=False)
    sort = forms.ChoiceField(label='sort by', widget=forms.Select, choices=SEARCH_SORT_OPTIONS)


class IssueDisplayForm(forms.ModelForm):
    class Meta:
        model = journal_models.Journal
        fields = (
            'display_issue_volume',
            'display_issue_number',
            'display_issue_year',
            'display_issue_title',
        )

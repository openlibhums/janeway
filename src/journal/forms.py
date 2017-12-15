__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from simplemathcaptcha.fields import MathCaptchaField
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

from core import models as core_models
from journal import models as journal_models


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
            #self.fields['recipient'].required = True

    class Meta:
        model = core_models.Contact
        fields = ('recipient', 'sender', 'subject', 'body')

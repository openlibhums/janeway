__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django import forms
from django.utils.translation import ugettext_lazy as _

from simplemathcaptcha.fields import MathCaptchaField

from core import models as core_models
from journal import models as journal_models


class JournalForm(forms.ModelForm):

    class Meta:
        model = journal_models.Journal
        fields = ('code', 'domain')


class ContactForm(forms.ModelForm):

    question_template = _('What is %(num1)i %(operator)s %(num2)i? ')
    are_you_a_robot = MathCaptchaField(label=_('Answer this question: '))

    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', None)
        super(ContactForm, self).__init__(*args, **kwargs)

        self.fields['are_you_a_robot'].required = True

        if subject:
            self.fields['subject'].initial = subject

    class Meta:
        model = core_models.Contact
        fields = ('recipient', 'sender', 'subject', 'body')

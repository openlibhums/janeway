from django.forms import (
    BooleanField,
    CharField,
    CheckboxInput,
    ModelForm,
    DateInput,
    HiddenInput,
    Form,
    widgets,
)
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from modeltranslation import forms as mt_forms, translator
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget
from simplemathcaptcha.fields import MathCaptchaField
from hcaptcha.fields import hCaptchaField

from submission import models as submission_models


class JanewayTranslationModelForm(mt_forms.TranslationModelForm):
    def __init__(self, *args, **kwargs):
        super(JanewayTranslationModelForm, self).__init__(*args, **kwargs)
        opts = translator.translator.get_options_for_model(self._meta.model)
        self.translated_field_names = opts.get_field_names()


class FakeModelForm(ModelForm):
    """ A form that can't be saved

    Usefull for rendering a sample form
    """

    def __init__(self, *args, disable_fields=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_fields = disable_fields
        if disable_fields is True:
            for field in self.fields:
                self.fields[field].widget.attrs["readonly"] = True

    def save(self, *args, **kwargs):
        raise NotImplementedError("FakeModelForm can't be saved")

    def clean(self, *args, **kwargs):
        if self.disable_fields is True:
            raise NotImplementedError(
                "FakeModelForm can't be cleaned: disable_fields is True",
            )
        return super().clean(*args, **kwargs)


class KeywordModelForm(ModelForm):
    """ A ModelForm for models implementing a Keyword M2M relationship """
    keywords = CharField(
            required=False, help_text=_("Hit Enter to add a new keyword."))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            current_keywords = self.instance.keywords.values_list(
                "word", flat=True)
            field = self.fields["keywords"]
            field.initial = ",".join(current_keywords)

    def save(self, commit=True, *args, **kwargs):
        posted_keywords = self.cleaned_data.get( 'keywords', '')

        instance = super().save(commit=commit, *args, **kwargs)
        instance.keywords.clear()

        if posted_keywords:
            keyword_list = posted_keywords.split(",")
            for i, keyword in enumerate(keyword_list):
                obj, _ = submission_models.Keyword.objects.get_or_create(
                    word=keyword)
                instance.keywords.add(obj)
        if commit:
            instance.save()
        return instance


class HTMLDateInput(DateInput):
    input_type = 'date'

    def __init__(self, **kwargs):
        kwargs["format"] = "%Y-%m-%d"
        super().__init__(**kwargs)


class CaptchaForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Used by simple math captcha
        self.question_template = None

        if settings.CAPTCHA_TYPE == 'simple_math':
            self.question_template = _('What is %(num1)i %(operator)s %(num2)i? ')
            captcha = MathCaptchaField(label=_('Answer this question: '))
        elif settings.CAPTCHA_TYPE == 'recaptcha':
            captcha = ReCaptchaField(widget=ReCaptchaWidget())
        elif settings.CAPTCHA_TYPE == 'hcaptcha':
            captcha = hCaptchaField()
        else:
            captcha = CharField(widget=HiddenInput, required=False)

        self.fields["captcha"] = captcha


class LeftCheckboxInput(CheckboxInput):
    """ A checkbox input that renders the actual checkbox left on the text"""
    def __init__(self, *args, **kwargs):
        self.choice_label = kwargs.pop('choice_label', '')
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        attrs = attrs or self.attrs
        label_attrs = ['class="checkbox-inline"']
        if 'id' in self.attrs:
            label_attrs.append(format_html('for="{}"', self.attrs['id']))
        label_for = mark_safe(' '.join(label_attrs))
        tag = super(CheckboxInput, self).render(name, value, attrs)
        return format_html('<label {0}>{1} {2}</label>', label_for, tag, self.choice_label)


class LeftBooleanField(BooleanField):
    widget = LeftCheckboxInput
    """ A BooleanField that uses the LeftCheckboxInput widget"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.label:
            if not self.widget.choice_label:
                self.widget.choice_label = self.label
            self.label = ''

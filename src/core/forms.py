__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import uuid

from django import forms
from django.forms.fields import Field
from django_summernote.widgets import SummernoteWidget
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from hvad.forms import TranslatableModelForm
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm

from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget
from simplemathcaptcha.fields import MathCaptchaField

from core import models, validators
from utils.logic import get_current_request
from journal import models as journal_models
from utils import setting_handler
from utils.forms import KeywordModelForm
from utils.logger import get_logger
from submission import models as submission_models

# This will set is_checkbox attribute to True for checkboxes.
# Usage:  {% if field.field.is_checkbox %}
setattr(Field, 'is_checkbox', lambda self: isinstance(self.widget, forms.CheckboxInput))

logger = get_logger(__name__)


class EditKey(forms.Form):
    def __init__(self, *args, **kwargs):
        key_type = kwargs.pop('key_type', None)
        value = kwargs.pop('value', None)
        super(EditKey, self).__init__(*args, **kwargs)

        if key_type == 'rich-text':
            self.fields['value'].widget = SummernoteWidget()
        elif key_type == 'boolean':
            self.fields['value'].widget = forms.CheckboxInput()
        elif key_type == 'integer':
            self.fields['value'].widget = forms.TextInput(attrs={'type': 'number'})
        elif key_type == 'file' or key_type == 'journalthumb':
            self.fields['value'].widget = forms.FileInput()
        elif key_type == 'text':
            self.fields['value'].widget = forms.Textarea()
        else:
            self.fields['value'].widget.attrs['size'] = '100%'

        self.fields['value'].initial = value
        self.fields['value'].required = False

    value = forms.CharField(label='')

    def clean(self):
        cleaned_data = self.cleaned_data

        return cleaned_data


class JournalContactForm(forms.ModelForm):

    class Meta:
        model = models.Contacts
        exclude = ('content_type', 'object_id', 'sequence',)


class EditorialGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        next_sequence = kwargs.pop('next_sequence', None)
        super(EditorialGroupForm, self).__init__(*args, **kwargs)

        if next_sequence:
            self.fields['sequence'].initial = next_sequence

    class Meta:
        model = models.EditorialGroup
        exclude = ('journal',)


class PasswordResetForm(forms.Form):

    password_1 = forms.CharField(widget=forms.PasswordInput, label=_('Password 1'))
    password_2 = forms.CharField(widget=forms.PasswordInput, label=_('Password 2'))

    def clean_password_2(self):
        password_1 = self.cleaned_data.get("password_1")
        password_2 = self.cleaned_data.get("password_2")
        if password_1 and password_2 and password_1 != password_2:
            raise forms.ValidationError(
                'Your passwords do not match.',
                code='password_mismatch',
            )

        return password_2


class RegistrationForm(forms.ModelForm):
    """ A form that creates a user, with no privileges,
    from the given username and password."""

    password_1 = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    password_2 = forms.CharField(widget=forms.PasswordInput, label=_('Repeat Password'))

    if settings.CAPTCHA_TYPE == 'simple_math':
        question_template = _('What is %(num1)i %(operator)s %(num2)i? ')
        are_you_a_robot = MathCaptchaField(label=_('Answer this question: '))
    elif settings.CAPTCHA_TYPE == 'recaptcha':
        are_you_a_robot = ReCaptchaField(widget=ReCaptchaWidget())
    else:
        are_you_a_robot = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = models.Account
        fields = ('email', 'salutation', 'first_name', 'middle_name',
                  'last_name', 'department', 'institution', 'country',)

    def clean_password_2(self):
        password_1 = self.cleaned_data.get("password_1")
        password_2 = self.cleaned_data.get("password_2")
        if password_1 and password_2 and password_1 != password_2:
            raise forms.ValidationError(
                'Your passwords do not match.',
                code='password_mismatch',
            )

        return password_2

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password_1"])
        user.is_active = False
        user.confirmation_code = uuid.uuid4()
        user.email_sent = timezone.now()

        if commit:
            user.save()

        return user


class EditAccountForm(forms.ModelForm):
    """ A form that creates a user, with no privileges, from the given username and password."""

    interests = forms.CharField(required=False)

    class Meta:
        model = models.Account
        exclude = ('email', 'username', 'activation_code', 'email_sent',
                   'date_confirmed', 'confirmation_code', 'is_active',
                   'is_staff', 'is_admin', 'date_joined', 'password',
                   'is_superuser')

    def save(self, commit=True):
        user = super(EditAccountForm, self).save(commit=False)

        posted_interests = self.cleaned_data['interests'].split(',')
        for interest in posted_interests:
            new_interest, c = models.Interest.objects.get_or_create(name=interest)
            user.interest.add(new_interest)

        for interest in user.interest.all():
            if interest.name not in posted_interests:
                user.interest.remove(interest)

        user.save()

        if commit:
            user.save()

        return user


class AdminUserForm(forms.ModelForm):

    class Meta:
        model = models.Account
        fields = ('email', 'is_active', 'is_staff', 'is_admin', 'is_superuser')

    def __init__(self, *args, **kwargs):
        active = kwargs.pop('active', None)
        request = kwargs.pop('request', None)
        super(AdminUserForm, self).__init__(*args, **kwargs)

        if not kwargs.get('instance', None):
            self.fields['is_active'].initial = True

        if active == 'add':
            self.fields['password_1'] = forms.CharField(widget=forms.PasswordInput, label="Password")
            self.fields['password_2'] = forms.CharField(widget=forms.PasswordInput, label="Repeat password")

        if request and not request.user.is_admin:
            self.fields.pop('is_staff', None)
            self.fields.pop('is_admin', None)

        if request and not request.user.is_superuser:
            self.fields.pop('is_superuser')

    def clean_password_2(self):
        password_1 = self.cleaned_data.get("password_1")
        password_2 = self.cleaned_data.get("password_2")

        if password_1 and password_2 and password_1 != password_2:
            raise forms.ValidationError(
                'Your passwords do not match.',
                code='password_mismatch',
            )

        if password_2 and not len(password_2) >= 12:
            raise forms.ValidationError(
                'Your password is too short, it should be 12 characters or greater in length.',
                code='password_to_short',
            )

        return password_2

    def save(self, commit=True):
        user = super(AdminUserForm, self).save(commit=False)
        user.username = self.cleaned_data['email']

        if self.cleaned_data.get('password_1'):
            user.set_password(self.cleaned_data["password_1"])
        user.save()

        if commit:
            user.save()

        return user


class GeneratedPluginSettingForm(forms.Form):

    def __init__(self, *args, **kwargs):
        settings = kwargs.pop('settings', None)
        super(GeneratedPluginSettingForm, self).__init__(*args, **kwargs)

        for field in settings:

            object = field['object']
            if field['types'] == 'char':
                self.fields[field['name']] = forms.CharField(widget=forms.TextInput(), required=False)
            elif field['types'] == 'rich-text' or field['types'] == 'text' or field['types'] == 'Text':
                self.fields[field['name']] = forms.CharField(widget=forms.Textarea, required=False)
            elif field['types'] == 'json':
                self.fields[field['name']] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                                                       choices=field['choices'],
                                                                       required=False)
            elif field['types'] == 'number':
                self.fields[field['name']] = forms.CharField(widget=forms.TextInput(attrs={'type': 'number'}))
            elif field['types'] == 'select':
                self.fields[field['name']] = forms.CharField(widget=forms.Select(choices=field['choices']))
            elif field['types'] == 'date':
                self.fields[field['name']] = forms.CharField(
                    widget=forms.DateInput(attrs={'class': 'datepicker'}))
            elif field['types'] == 'boolean':
                self.fields[field['name']] = forms.BooleanField(
                    widget=forms.CheckboxInput(attrs={'is_checkbox': True}),
                    required=False)

            self.fields[field['name']].initial = object.processed_value
            self.fields[field['name']].help_text = object.setting.description

    def save(self, journal, plugin, commit=True):
        for setting_name, setting_value in self.cleaned_data.items():
            setting_handler.save_plugin_setting(plugin, setting_name, setting_value, journal)


class GeneratedSettingForm(forms.Form):

    def __init__(self, *args, **kwargs):
        settings = kwargs.pop('settings', None)
        super(GeneratedSettingForm, self).__init__(*args, **kwargs)

        for field in settings:

            object = field['object']
            if object.setting.types == 'char':
                self.fields[field['name']] = forms.CharField(widget=forms.TextInput(), required=False)
            elif object.setting.types == 'rich-text' or object.setting.types == 'text':
                self.fields[field['name']] = forms.CharField(widget=forms.Textarea, required=False)
            elif object.setting.types == 'json':
                self.fields[field['name']] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                                                       choices=field['choices'],
                                                                       required=False)
            elif object.setting.types == 'number':
                self.fields[field['name']] = forms.CharField(widget=forms.TextInput(attrs={'type': 'number'}))
            elif object.setting.types == 'select':
                self.fields[field['name']] = forms.CharField(widget=forms.Select(choices=field['choices']))
            elif object.setting.types == 'date':
                self.fields[field['name']] = forms.CharField(
                    widget=forms.DateInput(attrs={'class': 'datepicker'}))
            elif object.setting.types == 'boolean':
                self.fields[field['name']] = forms.BooleanField(
                    widget=forms.CheckboxInput(attrs={'is_checkbox': True}),
                    required=False)

            self.fields[field['name']].label = object.setting.pretty_name
            self.fields[field['name']].initial = object.processed_value
            self.fields[field['name']].help_text = object.setting.description

    def save(self, journal, group, commit=True):
        for setting_name, setting_value in self.cleaned_data.items():
            setting_handler.save_setting('general', setting_name, journal, setting_value)


class JournalAttributeForm(KeywordModelForm):

    default_thumbnail = forms.FileField(required=False)
    press_image_override = forms.FileField(required=False)

    class Meta:
        model = journal_models.Journal
        fields = (
           'contact_info', 'header_image', 'default_cover_image',
           'default_large_image', 'favicon',
           'is_remote', 'remote_view_url', 'remote_submit_url',
           'disable_metrics_display', 'disable_article_images',
           'enable_correspondence_authors', 'full_width_navbar',
           'view_pdf_button',
        )


class PressJournalAttrForm(KeywordModelForm):
    default_thumbnail = forms.FileField(required=False)
    press_image_override = forms.FileField(required=False)

    class Meta:
        model = journal_models.Journal
        fields = (
            'contact_info', 'header_image', 'default_cover_image',
            'default_large_image', 'favicon', 'is_remote', 'is_conference',
            'remote_view_url', 'remote_submit_url', 'hide_from_press',
            'disable_metrics_display',
        )


class NotificationForm(forms.ModelForm):
    class Meta:
        model = journal_models.Notifications
        exclude = ('journal',)


class ArticleMetaImageForm(forms.ModelForm):
    class Meta:
        model = submission_models.Article
        fields = ('meta_image',)


class SectionForm(TranslatableModelForm):
    class Meta:
        model = submission_models.Section
        fields = ['name', 'plural', 'number_of_reviewers', 'is_filterable', 'sequence', 'section_editors', 'editors',
                  'public_submissions', 'indexing']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(SectionForm, self).__init__(*args, **kwargs)
        if request:
            self.fields['section_editors'].queryset = request.journal.users_with_role('section-editor')
            self.fields['section_editors'].required = False
            self.fields['editors'].queryset = request.journal.users_with_role('editor')
            self.fields['editors'].required = False


class QuickUserForm(forms.ModelForm):
    class Meta:
        model = models.Account
        fields = ('email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data["email"]
        if self.instance.email == email:
            return email
        try:
            models.Account.objects.get(email=email)
        except models.Account.DoesNotExist:
            return email
        raise forms.ValidationError(
            'This email address is already in use.'
        )


class LoginForm(forms.Form):
    user_name = forms.CharField(max_length=255, label="Email")
    user_pass = forms.CharField(max_length=255, label="Password", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        bad_logins = kwargs.pop('bad_logins', 0)
        super(LoginForm, self).__init__(*args, **kwargs)
        if bad_logins:
            logger.warning(
                "[FAILED_LOGIN:%s][FAILURES: %s]"
                "" % (self.fields["user_name"], bad_logins),
            )
        if bad_logins >= 3:
            self.fields['captcha'] = self.captcha_field
        else:
            self.fields['captcha'] = forms.CharField(widget=forms.HiddenInput(), required=False)

    @property
    def captcha_field(self):
        if settings.CAPTCHA_TYPE == 'simple_math':
            self.question_template = _('What is %(num1)i %(operator)s %(num2)i? ')
            return MathCaptchaField(label=_('Anti-spam captcha'))
        elif settings.CAPTCHA_TYPE == 'recaptcha':
            field = ReCaptchaField(widget=ReCaptchaWidget())
            field.label = "Anti-spam captcha"
            return field
        else:
            logger.warning(
                    "Unknown CAPTCHA_TYPE in settings: %s"
            "" % settings.CAPTCHA_TYPE
            )
            return self.no_cacptcha_field

    @property
    def no_captcha_field(self):
        return forms.CharField(widget=forms.HiddenInput(), required=False)


class FileUploadForm(forms.Form):
    file = forms.FileField()

    def __init__(self, *args, extensions=None, mimetypes=None, **kwargs):
        super().__init__(*args, **kwargs)
        validator = validators.FileTypeValidator(
                extensions=extensions,
                mimetypes=mimetypes,
        )
        self.fields["file"].validators.append(validator)


class UserCreationFormExtended(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationFormExtended, self).__init__(*args, **kwargs)
        self.fields['email'] = forms.EmailField(
            label=_("E-mail"),
            max_length=75,
        )


class XSLFileForm(forms.ModelForm):

    class Meta:
        model = models.XSLFile
        exclude = ["date_uploaded", "journal", "original_filename"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        request = get_current_request()

        if request:
            instance.journal = request.journal

        if commit:
            instance.save()

        return instance

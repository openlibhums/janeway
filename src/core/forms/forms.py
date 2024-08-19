__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import uuid
import json

from django import forms
from django.forms.fields import Field
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email, ValidationError

from tinymce.widgets import TinyMCE

from core import email, models, validators
from core.forms.fields import MultipleFileField, TagitField
from core.model_utils import JanewayBleachFormField, MiniHTMLFormField
from utils.logic import get_current_request
from journal import models as journal_models
from utils import render_template, setting_handler
from utils.forms import (
    KeywordModelForm,
    JanewayTranslationModelForm,
    CaptchaForm,
    HTMLDateInput,
)
from utils.logger import get_logger
from submission import models as submission_models

logger = get_logger(__name__)


class EditKey(forms.Form):
    def __init__(self, *args, **kwargs):
        self.key_type = kwargs.pop('key_type', None)
        value = kwargs.pop('value', None)
        super(EditKey, self).__init__(*args, **kwargs)

        if self.key_type == 'rich-text':
            self.fields['value'] = JanewayBleachFormField()
        elif self.key_type == 'mini-html':
            self.fields['value'] = MiniHTMLFormField()
        elif self.key_type == 'text':
            self.fields['value'].widget = forms.Textarea()
        elif self.key_type == 'char':
            self.fields['value'].widget = forms.TextInput()
        elif self.key_type in {'number', 'integer'}:
            # 'integer' is either a bug or used by a plugin
            self.fields['value'].widget = forms.TextInput(attrs={'type': 'number'})
        elif self.key_type == 'boolean':
            self.fields['value'] = forms.BooleanField(widget=forms.CheckboxInput)
        elif self.key_type == 'file' or self.key_type == 'journalthumb':
            self.fields['value'].widget = forms.FileInput()
        elif self.key_type == 'json':
            self.fields['value'].widget = forms.Textarea()
        else:
            self.fields['value'].widget.attrs['size'] = '100%'

        self.fields['value'].initial = value
        self.fields['value'].required = False
        self.fields['value'].label = ''

    value = forms.CharField(label='')

    def clean(self):
        cleaned_data = self.cleaned_data

        if self.key_type == 'json':
            try:
                json.loads(cleaned_data.get('value'))
            except json.JSONDecodeError as e:
                self.add_error(
                    'value',
                    f'JSON not valid: {e}',
                )

        return cleaned_data


class JournalContactForm(JanewayTranslationModelForm):
    def __init__(self, *args, **kwargs):
        next_sequence = kwargs.pop('next_sequence', None)
        super(JournalContactForm, self).__init__(*args, **kwargs)
        if next_sequence:
            self.fields['sequence'].initial = next_sequence

    class Meta:
        model = models.Contacts
        fields = ('name', 'email', 'role', 'sequence',)
        exclude = ('content_type', 'object_id',)


class EditorialGroupForm(JanewayTranslationModelForm):

    def __init__(self, *args, **kwargs):
        next_sequence = kwargs.pop('next_sequence', None)
        super(EditorialGroupForm, self).__init__(*args, **kwargs)
        if next_sequence:
            self.fields['sequence'].initial = next_sequence

    class Meta:
        model = models.EditorialGroup
        fields = ('name', 'description', 'sequence', 'display_profile_images')
        exclude = ('journal', 'press')


class PasswordResetForm(forms.Form):

    password_1 = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    password_2 = forms.CharField(widget=forms.PasswordInput, label=_('Repeat Password'))

    def clean_password_2(self):
        password_1 = self.cleaned_data.get("password_1")
        password_2 = self.cleaned_data.get("password_2")
        if password_1 and password_2 and password_1 != password_2:
            raise forms.ValidationError(
                'Your passwords do not match.',
                code='password_mismatch',
            )

        return password_2


class RegistrationForm(forms.ModelForm, CaptchaForm):
    """ A form that creates a user, with no privileges,
    from the given username and password."""

    password_1 = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    password_2 = forms.CharField(widget=forms.PasswordInput, label=_('Repeat Password'))
    register_as_reader = forms.BooleanField(
        label='Register for Article Notifications',
        help_text=_('Check this box if you would like to receive notifications of new articles published in this journal'),
        required=False,
    )

    class Meta:
        model = models.Account
        fields = ('email', 'salutation', 'first_name', 'middle_name',
                  'last_name', 'department', 'institution', 'country', 'orcid',)
        widgets = {'orcid': forms.HiddenInput() }

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal', None)
        super(RegistrationForm, self).__init__(*args, **kwargs)

        if not self.journal:
            self.fields.pop('register_as_reader')
        elif self.journal:
            send_reader_notifications = setting_handler.get_setting(
                'notifications',
                'send_reader_notifications',
                self.journal
            ).value
            if not send_reader_notifications:
                self.fields.pop('register_as_reader')

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
            if self.cleaned_data.get('register_as_reader') and self.journal:
                user.add_account_role(
                    role_slug="reader",
                    journal=self.journal,
                )

        return user


class EditAccountForm(forms.ModelForm):
    """ A form that creates a user, with no privileges, from the given username and password."""

    interests = forms.CharField(required=False)

    class Meta:
        model = models.Account
        exclude = ('email', 'username', 'activation_code', 'email_sent',
                   'date_confirmed', 'confirmation_code', 'is_active',
                   'is_staff', 'is_admin', 'date_joined', 'password',
                   'is_superuser', 'enable_digest')
        widgets = {
            'biography': TinyMCE(),
            'signature': TinyMCE(),
        }

    def save(self, commit=True):
        user = super(EditAccountForm, self).save(commit=False)
        user.clean()

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
            self.fields['password_2'] = forms.CharField(widget=forms.PasswordInput, label="Repeat Password")

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
            elif field['types'] == 'rich-text':
                self.fields[field['name']] = JanewayBleachFormField(
                    required=False,
               )
            elif field['types'] == 'mini-html':
                self.fields[field['name']] = MiniHTMLFormField(
                    required=False,
                )
            elif field['types'] in {'text', 'Text'}:
                # Keeping Text because a plugin may use it
                self.fields[field['name']] = forms.CharField(
                    widget=forms.Textarea,
                    required=False,
                )
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
        self.translatable_field_names = []
        for field in settings:
            object = field['object']

            if object.setting.types == 'char':
                self.fields[field['name']] = forms.CharField(widget=forms.TextInput(), required=False)
            elif object.setting.types == 'rich-text':
                self.fields[field['name']] = JanewayBleachFormField(
                    required=False,
                )
            elif object.setting.types == 'mini-html':
                self.fields[field['name']] = MiniHTMLFormField(
                    required=False,
                )
            elif object.setting.types == 'text':
                self.fields[field['name']] = forms.CharField(
                    widget=forms.Textarea,
                    required=False,
                )
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

            if object.setting.is_translatable:
                self.translatable_field_names.append(object.setting.name)

            self.fields[field['name']].label = object.setting.pretty_name
            self.fields[field['name']].initial = object.processed_value
            self.fields[field['name']].help_text = object.setting.description

    def save(self, journal, group, commit=True):
        for setting_name, setting_value in self.cleaned_data.items():
            setting_handler.save_setting(group, setting_name, journal, setting_value)


class JournalAttributeForm(JanewayTranslationModelForm, KeywordModelForm):
    class Meta:
        model = journal_models.Journal
        fields = (
           'contact_info',
           'is_remote',
           'remote_view_url',
           'remote_submit_url',
           'hide_from_press',
        )


class JournalImageForm(forms.ModelForm):
    default_thumbnail = forms.FileField(required=False)

    class Meta:
        model = journal_models.Journal
        fields = (
            'header_image', 'default_cover_image',
            'default_large_image', 'favicon', 'press_image_override',
            'default_profile_image',
        )


class JournalStylingForm(forms.ModelForm):
    class Meta:
        model = journal_models.Journal
        fields = (
            'full_width_navbar',
        )


class JournalSubmissionForm(forms.ModelForm):
    class Meta:
        model = journal_models.Journal
        fields = (
            'enable_correspondence_authors',
        )


class JournalArticleForm(forms.ModelForm):
    class Meta:
        model = journal_models.Journal
        fields = (
            'view_pdf_button',
            'disable_metrics_display',
            'disable_html_downloads',
        )


class PressJournalAttrForm(KeywordModelForm, JanewayTranslationModelForm):
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
        widgets = {
            'active': forms.CheckboxInput(
                attrs={
                    'is_checkbox': True,
                }
            ),
        }


class ArticleMetaImageForm(forms.ModelForm):
    class Meta:
        model = submission_models.Article
        fields = ('meta_image',)


class SectionForm(JanewayTranslationModelForm):
    class Meta:
        model = submission_models.Section
        fields = [
            'name', 'plural', 'number_of_reviewers',
            'is_filterable', 'sequence', 'section_editors',
            'editors', 'public_submissions', 'indexing',
            'auto_assign_editors',
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(SectionForm, self).__init__(*args, **kwargs)
        if request:
            self.fields['section_editors'].queryset = request.journal.users_with_role(
                'section-editor',
            )
            self.fields['section_editors'].required = False
            self.fields['editors'].queryset = request.journal.users_with_role('editor')
            self.fields['editors'].required = False


class QuickUserForm(forms.ModelForm):
    class Meta:
        model = models.Account
        fields = ('email', 'salutation', 'first_name', 'last_name', 'institution',)


class LoginForm(CaptchaForm):
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
        if bad_logins <= 3:
            self.fields['captcha'] = forms.CharField(widget=forms.HiddenInput(), required=False)


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


class AccessRequestForm(forms.ModelForm):

    class Meta:
        model = models.AccessRequest
        fields = ('text',)
        labels = {
            'text': 'Supporting Information',
        }

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal', None)
        self.repository = kwargs.pop('repository', None)
        self.user = kwargs.pop('user')
        self.role = kwargs.pop('role')
        super(AccessRequestForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        access_request = super().save(commit=False)
        access_request.journal = self.journal
        access_request.repository = self.repository
        access_request.user = self.user
        access_request.role = self.role

        if commit:
            access_request.save()

        return access_request


class CBVFacetForm(forms.Form):

    def __init__(self, *args, **kwargs):
        # This form populates the facets that users can filter results on
        # If you pass a separate facet_queryset into kwargs, the form is
        # the same regardless of how the result queryset changes
        # To have the facets dynamically contract based on the result queryset,
        # do not pass anything for facet_queryset into kwargs.

        self.id = 'facet_form'
        self.queryset = kwargs.pop('queryset')
        self.facets = kwargs.pop('facets')
        self.facet_queryset = kwargs.pop('facet_queryset', None)
        if not self.facet_queryset:
            self.facet_queryset = self.queryset
        self.fields = {}

        super().__init__(*args, **kwargs)

        for facet_key, facet in self.facets.items():

            if facet['type'] == 'foreign_key':

                # Note: This retrieval is written to work even for sqlite3.
                # It might be rewritten differently if sqlite3 support isn't needed.
                if self.facet_queryset:
                    column = self.facet_queryset.values_list(facet_key, flat=True)
                else:
                    column = self.queryset.values_list(facet_key, flat=True)
                values_list = list(filter(bool, column))
                choice_queryset = facet['model'].objects.filter(pk__in=values_list)

                if facet.get('order_by'):
                    choice_queryset = self.order_by(choice_queryset, facet, values_list)

                choices = []
                for each in choice_queryset:
                    label = getattr(each, facet["choice_label_field"])
                    count = values_list.count(each.pk)
                    label_with_count = f'{label} ({count})'
                    choices.append((each.pk, label_with_count))
                self.fields[facet_key] = forms.ChoiceField(
                    widget=forms.widgets.CheckboxSelectMultiple,
                    choices=choices,
                    required=False,
                )

            elif facet['type'] == 'charfield_with_choices':
                # Note: This retrieval is written to work even for sqlite3.
                # It might be rewritten differently if sqlite3 support isn't needed.

                if self.facet_queryset:
                    queryset = self.facet_queryset
                else:
                    queryset = self.queryset
                column = []
                values_list = []
                lookup_parts = facet_key.split('.')
                for obj in queryset:
                    for part in lookup_parts:
                        if obj:
                            try:
                                result = getattr(obj, part)
                                obj = result
                            except:
                                result = None

                    if result != None:
                        values_list.append(result)
                    elif result == None and 'default' in facet:
                        values_list.append(facet['default'])

                unique_values = set(values_list)
                choices = []
                model_choice_dict = dict(facet['model_choices'])
                for value in unique_values:
                    label = model_choice_dict.get(value, value)
                    count = values_list.count(value)
                    label_with_count = f'{label} ({count})'
                    choices.append((value, label_with_count))
                self.fields[facet_key] = forms.ChoiceField(
                    widget=forms.widgets.CheckboxSelectMultiple,
                    choices=choices,
                    required=False,
                )

            elif facet['type'] == 'date_time':
                self.fields[facet_key] = forms.DateTimeField(
                    required=False,
                    widget=forms.DateTimeInput(
                        attrs={'type': 'datetime-local'}
                    ),
                )

            elif facet['type'] == 'date':
                self.fields[facet_key] = forms.DateField(
                    required=False,
                    widget=forms.DateInput(
                        attrs={'type': 'date'}
                    ),
                )

            elif facet['type'] == 'integer':
                self.fields[facet_key] = forms.IntegerField(
                    required=False,
                )

            elif facet['type'] == 'search':
                self.fields[facet_key] = forms.CharField(
                    required=False,
                    widget=forms.TextInput(
                        attrs={'type': 'search'}
                    ),
                )

            elif facet['type'] == 'boolean':
                self.fields[facet_key] = forms.ChoiceField(
                    widget=forms.widgets.RadioSelect,
                    choices=[(1, 'Yes'), (0, 'No')],
                    required=False,
                )

            self.fields[facet_key].label = facet['field_label']

    def order_by(self, queryset, facet, fks):
        order_by = facet.get('order_by')
        if order_by != 'facet_count' and order_by in facet['model']._meta.get_fields():
            queryset = queryset.order_by(order_by)
        elif order_by == 'facet_count':
            sorted_fk_tuples = sorted(
                [(fk, fks.count(fk)) for fk in fks],
                key=lambda x:x[1],
                reverse=True,
            )
            sorted_fks = [tup[0] for tup in sorted_fk_tuples]
            queryset = sorted(
                queryset,
                key=lambda x: sorted_fks.index(x.pk)
            )

        # Note: There is no way yet to sort on the result of a 
        # function property like journal.name

        return queryset


class ConfirmableForm(forms.Form):
    """
    Adds a modal at form submission asking
    the user a question and showing them
    potential problems with how they
    completed the form. Different from
    validation because potential errors
    are more nuanced than invalid data.

    The modal always appears on submission,
    even if there are no potential errors.
    For a version where the modal only appears
    if there are errrors, see ConfirmableIfErrorsForm.
    """

    CONFIRMABLE_BUTTON_NAME = 'confirmable'
    CONFIRMED_BUTTON_NAME = 'confirmed'
    QUESTION = _('Are you sure?')

    def __init__(self, *args, **kwargs):
        self.modal = None
        super().__init__(*args, **kwargs)

    def is_valid(self, *args, **kwargs):
        parent_return = super().is_valid(*args, **kwargs)
        if self.CONFIRMABLE_BUTTON_NAME in self.data:
            self.create_modal()
        return parent_return

    def create_modal(self):

        self.modal = {
            'id': 'confirm_modal',
            'confirmed_button_name': self.CONFIRMED_BUTTON_NAME,
            'question': self.QUESTION,
            'potential_errors': self.check_for_potential_errors(),
        }

    def check_for_potential_errors(self):
        return []

    def check_for_inactive_account(self, account):
        if not isinstance(account, models.Account):
            try:
                account = models.Account.objects.get(id=account)
            except models.Account.DoesNotExist:
                return 'Could not check account status'
        if not account.is_active:
            return _('The account belonging to %(email)s has not yet been activated, ' \
                     'so the recipient of this assignment may not be able ' \
                     'to log in and view it.') % {'email': account.email}

    def is_confirmed(self):
        return self.CONFIRMED_BUTTON_NAME in self.data


class ConfirmableIfErrorsForm(ConfirmableForm):
    """
    A variant of ConfirmableForm
    that only shows the modal if
    there are potential errors.
    Otherwise it submits the form.
    """

    def create_modal(self):
        if self.check_for_potential_errors():
            super().create_modal()

    def is_confirmed(self):
        if self.check_for_potential_errors():
            return super().is_confirmed()
        else:
            return True


class EmailForm(forms.Form):
    cc = TagitField(
        required=False,
        max_length=10000,
    )
    bcc = TagitField(
        required=False,
        max_length=10000,
    )
    subject = forms.CharField(max_length=1000)
    body = forms.CharField(widget=TinyMCE)
    attachments = MultipleFileField(required=False)

    def clean_cc(self):
        cc = self.cleaned_data['cc']
        return self.email_sequence_cleaner("cc", cc)

    def clean_bcc(self):
        cc = self.cleaned_data['bcc']
        return self.email_sequence_cleaner("bcc", cc)

    def email_sequence_cleaner(self, field, email_seq):
        if not email_seq or email_seq  == '':
            return tuple()

        for address in email_seq:
            try:
                validate_email(address)
            except ValidationError:
                self.add_error(field, 'Invalid email address ({}).'.format(address))

        return email_seq

    def as_dataclass(self):
        return email.EmailData(**self.cleaned_data)


class FullEmailForm(EmailForm):
    """ An email form that includes the To field
    """
    to = TagitField(
        required=True,
        max_length=10000,
    )

    field_order = ['to', 'cc', 'bcc', 'subject', 'body', 'attachments']

    def clean_to(self):
        to = self.cleaned_data['to']
        return self.email_sequence_cleaner("to", to)


class SettingEmailForm(EmailForm):
    """ An Email form that populates initial data using Janeway email settings

    During initialization, the email and subject settings are retrieved,
    matching the given setting_name
    :param setting_name: The name of the setting (Group must be email)
    :param email_context: A dict of the context required to populate the email
    :param request: The instance of this HttpRequest
    :param journal: (Optional) an instance of journal.models.Journal
    """
    def __init__(self, *args, **kwargs):
        setting_name = kwargs.pop("setting_name")
        email_context = kwargs.pop("email_context", {})
        subject_setting_name = "subject_" + setting_name
        request = kwargs.pop("request")
        journal = kwargs.pop("journal", None) or request.journal
        initial_subject = setting_handler.get_email_subject_setting(
            setting_name=subject_setting_name,
            journal=journal,
        )

        super().__init__(*args, **kwargs)
        self.fields["subject"].initial = initial_subject
        self.fields["body"].initial = render_template.get_message_content(
            request,
            email_context,
            setting_name,
        )


class FullSettingEmailForm(SettingEmailForm, FullEmailForm):
    """ A setting-based email form that includes the To field
    """
    pass


class SimpleTinyMCEForm(forms.Form):
    """ A one-field form for populating a TinyMCE textarea
    """

    def __init__(self, field_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[field_name] = forms.CharField(widget=TinyMCE)

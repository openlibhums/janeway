from core import forms as core_forms


class ConfirmArchivingForm(core_forms.ConfirmableForm):
    CONFIRMABLE_BUTTON_NAME = 'archive'
    CONFIRMED_BUTTON_NAME = 'confirmed'
    QUESTION = 'Are you certain you want to archive this article?'

from modeltranslation.translator import register, TranslationOptions

from core import models


@register(models.SettingValue)
class SettingValueTranslationOptions(TranslationOptions):
    fields = ("value",)


@register(models.EditorialGroup)
class EditorialGroupTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
    )


@register(models.ContactPerson)
class ContactTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "role",
    )

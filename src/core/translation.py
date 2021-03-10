from modeltranslation.translator import register, TranslationOptions

from core import models


@register(models.SettingValue)
class SettingValueTranslationOptions(TranslationOptions):
    fields = ('value',)

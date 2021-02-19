from modeltranslation.translator import register, TranslationOptions
from utils import models


@register(models.PluginSettingValue)
class PluginSettingValueTranslationOptions(TranslationOptions):
    fields = ('value',)

from django.conf import settings

from modeltranslation.translator import register, TranslationOptions

from submission import models


@register(models.Section)
class SectionTranslationOptions(TranslationOptions):
    fields = ('name', 'plural')

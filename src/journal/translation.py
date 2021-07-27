from modeltranslation.translator import register, TranslationOptions

from journal import models


@register(models.Journal)
class JournalTranslationOptions(TranslationOptions):
    fields = ('contact_info',)

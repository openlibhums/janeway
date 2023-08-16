from modeltranslation.translator import register, TranslationOptions

from journal import models


@register(models.Journal)
class JournalTranslationOptions(TranslationOptions):
    fields = ('contact_info',)


@register(models.Issue)
class IssueTranslationOptions(TranslationOptions):
    fields = ('cached_display_title',)

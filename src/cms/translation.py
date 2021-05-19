from modeltranslation.translator import register, TranslationOptions

from cms import models


@register(models.Page)
class PageTranslationOptions(TranslationOptions):
    fields = ('display_name', 'content')


@register(models.NavigationItem)
class NavigationItemTranslationOptions(TranslationOptions):
    fields = ('link_name',)


@register(models.SubmissionItem)
class SubmissionItemTranslationOption(TranslationOptions):
    fields = ('title', 'text')

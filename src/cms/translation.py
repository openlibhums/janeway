from modeltranslation.translator import register, TranslationOptions
from simple_history import register as register_history

from cms import models


@register(models.Page)
class PageTranslationOptions(TranslationOptions):
    fields = ('display_name', 'content')


# This adds a history field to models.Page
register_history(models.Page)


@register(models.NavigationItem)
class NavigationItemTranslationOptions(TranslationOptions):
    fields = ('link_name',)


@register(models.SubmissionItem)
class SubmissionItemTranslationOption(TranslationOptions):
    fields = ('title', 'text')

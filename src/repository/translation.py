from modeltranslation.translator import register, TranslationOptions

from repository import models


@register(models.Preprint)
class PreprintTranslationOptions(TranslationOptions):
    fields = ("title", "abstract")


@register(models.PreprintVersion)
class PreprintVersionTranslationOptions(TranslationOptions):
    fields = ("title", "abstract")


@register(models.VersionQueue)
class VersionQueueTranslationOptions(TranslationOptions):
    fields = ("title", "abstract")

from django.conf import settings

from modeltranslation.translator import register, TranslationOptions
from simple_history import register as register_history

from comms import models


@register(models.NewsItem)
class NewsItemTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'body',
        'custom_byline',
    )

# Registering NewsItem for history in a model translations compatible manner
register_history(models.NewsItem)
from django.utils import timezone

from utils import setting_handler
from django.db.models import Q


def yield_homepage_element_context(request, homepage_elements):
    from comms import models as comms_models
    from utils import models as utils_models
    if homepage_elements is not None and homepage_elements.filter(
            name='News').exists():

        # If we only have a press and it has news items set, use them.
        if not request.journal and request.press.carousel_news_items.all():
            return {'news_items': request.press.carousel_news_items.all()}

        plugin = utils_models.Plugin.objects.get(name='News')
        number_of_articles = setting_handler.get_plugin_setting(
            plugin,
            'number_of_articles',
            request.journal if request.journal else None).value
        number_of_articles = int(
            number_of_articles) if number_of_articles else 2

        news_items = comms_models.NewsItem.objects.filter(
            (Q(content_type=request.model_content_type) & Q(
                object_id=request.site_type.id)) &
            (Q(start_display__lte=timezone.now()) | Q(start_display=None)) &
            (Q(end_display__gte=timezone.now()) | Q(end_display=None))
        ).order_by('-posted')[:number_of_articles]

        return {'news_items': news_items}
    else:
        return {}

from django import template
from django.conf import settings
from django.utils.html import mark_safe

from importlib import import_module

from utils.logger import get_logger

logger = get_logger(__name__)
register = template.Library()


@register.simple_tag(takes_context=True)
def hook(context, hook_name, *args, **kwargs):
    try:
        html = ''
        for hook in settings.PLUGIN_HOOKS.get(hook_name, []):
            hook_module = import_module(hook.get('module'))
            function = getattr(hook_module, hook.get('function'))
            html = html + function(context, *args, **kwargs)

        return mark_safe(html)
    except Exception as e:
        logger.error('Error rendering hook {0}: {1}'.format(hook_name, e))

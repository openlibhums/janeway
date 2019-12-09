from django import template

from hijack.templatetags.hijack_tags import _render_hijack_notification

register = template.Library()


@register.simple_tag(takes_context=True)
def janeway_hijack_notification(context):
    request = context.get('request')
    template_name = 'common/elements/hijack-notification.html'
    return _render_hijack_notification(request, template_name=template_name)

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def journal_url(context, url_name=None, *args):
    request = context.get('request')
    if url_name is not None:
        path = reverse(url_name, args=args)
    else:
        path = None

    if request and request.journal:
        return request.journal.site_url(path=path)
    else:
        return path


@register.simple_tag(takes_context=True)
def journal_base_url(context, journal):
    return journal.site_url()

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def journal_url(context, url_name, *args):
    request = context['request']
    try:
        url = reverse(url_name, args=args)
        return '{0}{1}'.format(request.journal.full_url(request), url)
    except NoReverseMatch:
        return 'URL not matched.'


@register.simple_tag(takes_context=True)
def journal_base_url(context, journal):
    request = context['request']

    return journal.full_url(request)

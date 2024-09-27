from django import template

from utils.orcid import build_redirect_uri
from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def orcid_redirect_uri(context, action):
    request = context.get('request')
    if request:
        return build_redirect_uri(request.site_type, action=action)
    else:
        return ""

@register.simple_tag(takes_context=True)
def orcid_login_url(context, action):
    request = context.get('request')
    if request:
        redirect = build_redirect_uri(request.site_type, action=action)
        return f"{ settings.ORCID_URL }?client_id={ settings.ORCID_CLIENT_ID }&response_type=code&scope=/authenticate&redirect_uri={redirect}"
    else:
        return ""


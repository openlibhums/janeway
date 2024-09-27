from django import template

from utils.orcid import build_redirect_uri

register = template.Library()


@register.simple_tag(takes_context=True)
def orcid_redirect_uri(context, action="login"):
    request = context.get('request')
    if request:
        return build_redirect_uri(request.site_type, action=action)
    else:
        return ""


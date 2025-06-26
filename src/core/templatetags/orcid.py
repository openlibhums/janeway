from django import template

from core.logic import reverse_with_next
from utils.orcid import build_redirect_uri
from utils.logic import add_query_parameters_to_url

register = template.Library()


@register.simple_tag(takes_context=True)
def orcid_redirect_uri(context, action="login"):
    """
    This template tag is deprecated.
    Its logic now handled in core.views.user_login_orcid
    rather than templates.
    """
    raise DeprecationWarning(
        'This template tag is deprecated. See core.views.user_login_orcid.'
    )
    request = context.get('request')
    if request:
        return build_redirect_uri(request.site_type, action=action)
    else:
        return ""


@register.simple_tag(takes_context=True)
def url_with_next_and_orcid_action(context, url_name, action="login"):
    request = context.get('request')
    next_url = request.GET.get('next', '')
    url = reverse_with_next(url_name, next_url)
    return add_query_parameters_to_url(url, {'action': action})

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
def repository_url(context, url_name=None, *args):
    request = context.get('request')
    if url_name is not None:
        path = reverse(url_name, args=args)
    else:
        path = None

    if request and request.repository:
        return request.repository.site_url(path=path)
    else:
        return path

@register.simple_tag(takes_context=True)
def site_url(context, url_name=None, *args):
    request = context.get('request')
    if url_name is not None:
        path = reverse(url_name, args=args)
    else:
        path = None

    if request and request.site_type:
        return request.site_type.site_url(path=path)
    else:
        return path


@register.simple_tag
def stateless_site_url(site, url_name=None, query=None, *args):
    """ A tag for constructing a url for a site without global request state
    This should eventually become the canonical site builder for all other
    tags in this file
    :param site: The site model instance for which to construct the url
    :type site: core.model_utils.AbstractSiteModel
    :param url_name: A django url name to match
    :type url_name: str
    :param query: An encoded url querystring
    :type query: str
    :param *args: additional arguments for reversing the url by name
    """
    if url_name is not None:
        path = reverse(url_name, args=args)
    else:
        path = None

    return site.site_url(query=query, path=path)


@register.simple_tag(takes_context=True)
def journal_base_url(context, journal):
    return journal.site_url()


@register.simple_tag
def external_journal_url(journal, url_name=None, *args):
    if url_name is not None:
        path = reverse(url_name, args=args)
    else:
        path = None

    return journal.site_url(path=path)


@register.simple_tag(takes_context=True)
def build_absolute_uri(context, relative_url, *args):
    request = context.get('request')
    return request.build_absolute_uri(relative_url)

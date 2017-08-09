from django.conf import settings
from django.core.urlresolvers import reverse as django_reverse
from django.utils.encoding import iri_to_uri

from core.middleware import GlobalRequestMiddleware


def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None):
    """
    This monkey patch will add the journal_code to reverse kwargs if the URL_CONFIG setting is set to 'patch'
    """

    local_request = GlobalRequestMiddleware.get_current_request()

    if settings.URL_CONFIG == 'path':
        kwargs['journal_code'] = local_request.journal.code if local_request.journal else 'press'

    url = django_reverse(viewname, urlconf, args, kwargs, prefix)

    # Ensure any unicode characters in the URL are escaped.
    return iri_to_uri(url)

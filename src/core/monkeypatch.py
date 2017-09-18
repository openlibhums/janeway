from django.conf import settings
from django.core.urlresolvers import reverse as django_reverse
from django.utils.encoding import iri_to_uri

from core.middleware import GlobalRequestMiddleware


def reverse(viewname, urlconf=None, args=None, kwargs=None, current_app=None):
    """
    This monkey patch will add the journal_code to reverse kwargs if the URL_CONFIG setting is set to 'patch'
    """

    if not viewname.startswith('djdt'):
        local_request = GlobalRequestMiddleware.get_current_request()

        if settings.URL_CONFIG == 'path':
            code = local_request.journal.code if local_request.journal else 'press'
            if kwargs and not args:
                kwargs['journal_code'] = code
            else:
                kwargs = {'journal_code': code}

            # Drop kwargs if user is accessing admin site.
            if local_request.path.startswith('/admin/'):
                kwargs.pop('journal_code')

            # Drop kwargs if we have args (most likely from the template
            if args:
                kwargs = None
                if settings.URL_CONFIG == 'path' and not local_request.path.startswith('/admin/'):
                    args = tuple([code] + [x for x in args])
                else:
                    args = args

    url = django_reverse(viewname, urlconf, args, kwargs, current_app)

    # Ensure any unicode characters in the URL are escaped.
    return iri_to_uri(url)

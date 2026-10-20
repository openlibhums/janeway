__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from hashlib import sha1

from django.core.cache import cache as django_cache
from django.urls import get_script_prefix
from django.utils.functional import cached_property


def make_cache_key(f, args, kwargs, prefix=""):
    return sha1(
        prefix.encode("utf-8")
        + f.__module__.encode("utf-8")
        + f.__name__.encode("utf-8")
        + str(args).encode("UTF-8")
        + str(kwargs).encode("UTF-8")
    ).hexdigest()


def get_or_set_cache(key, f, args, kwargs, seconds):
    result = django_cache.get(key)
    if result is None:
        result = f(*args, **kwargs)
        django_cache.set(key, result, seconds)

    return result


def get_site_cache_key():
    """Identifies the site being served by the current request, if any

    Script Prefix is included to disambiguate path and domain mode
    """
    from utils.logic import get_current_request

    request = get_current_request()
    if request is None:
        return ""
    site = getattr(request, "site_object", None) or getattr(request, "site_type", None)
    if site is None:
        return ""
    return "%s:%s:%s" % (site._meta.label_lower, site.pk, get_script_prefix())


def cache(seconds=900):
    def do_cache(f):
        def y(*args, **kwargs):
            key = make_cache_key(f, args, kwargs)
            return get_or_set_cache(key, f, args, kwargs, seconds)

        return y

    return do_cache


def site_cache(seconds=900):
    """Like `cache`, but a request serving a site gets its own cache entries

    When there is a request in context with a site object set, the site and
    the path it is being served under become part of the cache key.
    """

    def do_cache(f):
        def y(*args, **kwargs):
            key = make_cache_key(f, args, kwargs, prefix=get_site_cache_key())
            return get_or_set_cache(key, f, args, kwargs, seconds)

        return y

    return do_cache


class mutable_cached_property(cached_property):
    """Expands django's cached property to allow property mutation

    A property mutation (__set__) will clear the previously cached value
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fsetter = None

    def __set__(self, obj, value):
        if self.fsetter is None:
            raise AttributeError(f"property '{self.name}' has no setter")
        self.fsetter(obj, value)
        obj.__dict__[self.name] = self.real_func(obj)

    def setter(self, fsetter):
        prop = type(self)(self.func, self.name)
        prop.setter = self.fsetter = fsetter
        return prop

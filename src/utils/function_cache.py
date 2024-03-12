__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from hashlib import sha1

from django.core.cache import cache as django_cache
from django.utils.functional import cached_property


def cache(seconds=900):

    def do_cache(f):
        def y(*args, **kwargs):
            f_module = f.__module__.encode('utf-8')
            f_name = f.__name__.encode('utf-8')
            key = sha1(f_module + f_name + str(args).encode('UTF-8') + str(kwargs).encode('UTF-8')).hexdigest()
            result = django_cache.get(key)
            if result is None:
                result = f(*args, **kwargs)
                django_cache.set(key, result, seconds)

            return result
        return y
    return do_cache


class mutable_cached_property(cached_property):
    """ Expands django's cached property to allow property mutation

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


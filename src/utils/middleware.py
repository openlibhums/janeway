__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import threading
_local = threading.local()


class ThemeEngineMiddleware(object):
    """ Handles theming through middleware
    """

    def process_request(self, request):
        _local.request = request

    def process_response(self, request, response):
        if hasattr(_local, 'request'):
            del _local.request
        return response

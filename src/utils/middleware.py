__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import resource
import threading
import time
from utils.logger import get_logger

logger = get_logger(__name__)

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


class TimeMonitoring(object):
    """Monitors the resource usage of a request/response cycle """
    def __init__(self):
        self.usage_start = None

    def process_request(self, _request):
        self.usage_start = self._get_usage()

    def process_response(self, _request, response):
        if self.usage_start is not None:
            diff_usage = self._diff_usages(self.usage_start)
            logger.info("Request took %0.3f (%0.3fu, %0.3fs)" % diff_usage)

        return response

    @classmethod
    def _diff_usages(cls, start, end=None):
        end = end or cls._get_usage()
        return tuple(b-a for a,b in zip(start, end))

    @staticmethod
    def _get_usage():
        utime, stime, *_ = resource.getrusage(resource.RUSAGE_THREAD)
        return (time.time(), utime, stime)


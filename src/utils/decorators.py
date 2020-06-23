"""
Utility decorators
"""
__copyright__ = "Copyright 2020 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import time
from functools import wraps

from utils.logger import get_logger


logger = get_logger(__name__)


def retry(attempts=3, throttle=0, exc=Exception):
    """ Retries calling a function when certain exceptions are raised
    :param attempts: maximum number of times to retry
    :param throttle_ms: optional throttling between calls in seconds
    :param exc: An exception (or tuple of exceptions) on which to retry
    """
    def wrapper(f):
        f_name = f.__name__
        msg = "%s failed with %s: %s, Retrying in %d s..."
        @wraps(f)
        def decorator(*args, **kwargs):
            tries = 1
            while tries < attempts:
                try:
                    return f(*args, **kwargs)
                except exc as e:
                    logger.warning(msg % (f_name, type(e), e, throttle))
                    if throttle:
                        logger.debug("Sleeping thread for %s" % throttle)
                        time.sleep(throttle)
                finally:
                    tries +=1
            return f(*args, **kwargs)

        return decorator
    return wrapper

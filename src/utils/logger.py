"""
Janeway logging utilities and main logger
"""
import logging
import threading


class LogPrefix(object):
    """ A logging prefix scoped for the current thread """
    _local = threading.local()

    @property
    def rendered_prefix(self):
        try:
            return self._local.prefix
        except AttributeError:
            self._local.prefix = ""
            return self._local.prefix

    @rendered_prefix.setter
    def rendered_prefix(self, val):
        self._local.prefix = val

    @property
    def _parts(self):
        try:
            return self._local.parts
        except AttributeError:
            self._local.parts = []
        return self._local.parts

    def push(self, item):
        self._parts.append(str(item))
        self.update()

    def pop(self):
        self._parts.pop()
        self.update()

    def update(self):
        self.rendered_prefix = ":".join(self._parts)

    def set(self, *parts):
        self._local.parts = list(parts)
        self.update()

    def do_prefix(self, msg):
        if _prefix.rendered_prefix:
            return "[%s] %s" % (self.rendered_prefix, msg)
        else:
            return msg


_prefix = LogPrefix()


class PrefixedLoggerAdapter(logging.LoggerAdapter):
    """ Adds the current prefix to the log line"""
    def process(self, msg, extra):
        return _prefix.do_prefix(msg), extra

    def push_prefix(self, item):
        _prefix.push(item)

    def pop_prefix(self):
        _prefix.pop()

    def set_prefix(self, *values):
        _prefix.set(*values)


def get_logger(logger_name, extra=None):
    logger = logging.getLogger(logger_name)
    return PrefixedLoggerAdapter(logger, extra or {})

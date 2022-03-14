from contextlib import ContextDecorator


class allow_mutating_GET(ContextDecorator):
    """CAUTION: Think twice before considering using this"""

    def __init__(self, request):
        self.request = request
        self._mutable = self.request.GET._mutable

    def __enter__(self):
        self.request.GET._mutable = True
        return self

    def __exit__(self, *exc):
        self.request.GET._mutable = self._mutable

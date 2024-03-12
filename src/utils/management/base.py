try:
    import cProfile as profile
except ImportError:
    import profile
import inspect
import io
import os
import time
import pstats

from django.conf import settings
from django.core.management.base import BaseCommand


class ProfiledCommand(BaseCommand):
    """ A base class for commands that can be profiled with --profile
    When the --profile flag is present, the command execution will be wrapped
    inside a profiler run. At the end of the command, the results of the
    profiler are printed to stdout and written to a temporary file. The file
    can then be visualised with tools like snakeviz
    """

    def add_arguments(self, parser):
        parser.add_argument('--profile', action="store_true")

    def execute(self, *args, **options):
        do_profile = options.pop("profile", False)
        if do_profile:
            profiler = profile.Profile()
            profiler.enable()
            super().execute(*args, **options)
            profiler.disable()
            s_io=io.StringIO()
            stats = pstats.Stats(profiler, stream=s_io).sort_stats("ncalls")
            stats.print_stats()

            # Flush to a file
            py_filename = inspect.getfile(self.__class__)
            command = os.path.basename(py_filename)
            stamp = time.time()
            filename = f"{command}-{stamp}.prof"
            path = os.path.join(settings.BASE_DIR, 'files', 'temp', filename)
            profiler.dump_stats(path)
            print(f"Profiling written to: {path}")
        else:
            super().execute(*args, **options)

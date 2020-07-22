from functools import wraps

from django.shortcuts import redirect, reverse


def frontend_enabled(func):
    """
    If journal.disable_front_end is enabled this decorator redirects to the
    submission page.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    @wraps(func)
    def frontend_enabled_wrapper(request, *args, **kwargs):
        if request.journal and request.journal.disable_front_end:
            return redirect(
                reverse(
                    'journal_submissions'
                )
            )
        return func(request, *args, **kwargs)

    return frontend_enabled_wrapper

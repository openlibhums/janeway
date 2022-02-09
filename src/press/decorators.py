from functools import wraps

from django.shortcuts import redirect, reverse


def journals_enabled(func):
    """
    If press.disable_journals is enabled this decorator redirects to the
    press home page.
    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    @wraps(func)
    def disable_journals_wrapper(request, *args, **kwargs):
        if request.press and not request.press.disable_journals:
            return func(request, *args, **kwargs)

        return redirect(
            reverse(
                'website_index'
            )
        )

    return disable_journals_wrapper
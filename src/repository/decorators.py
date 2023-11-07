from functools import wraps

from django.shortcuts import redirect, reverse
from django.contrib import messages


def headless_mode_check(func):
    """
    If request.repository.headless_mode is enabled this decorator
    redirects to the repo dashboard.
    :param func: the function to callback from the decorator
    :return: either the function call or raises an HttpRedirect
    """

    @wraps(func)
    def headless_mode_check_wrapper(request, *args, **kwargs):
        if request.repository and request.repository.headless_mode:
            messages.add_message(
                request,
                messages.INFO,
                'Redirected to dashboard. This repository runs in headless'
                ' mode.',
            )
            return redirect(
                reverse(
                    'repository_dashboard'
                )
            )
        return func(request, *args, **kwargs)

    return headless_mode_check_wrapper

from django.shortcuts import reverse, redirect

from plugins.typesetting import models
from security.decorators import base_check, deny_access


def proofreader_for_article_required(func):
    """
    Checks that the current user is the proofreader for the current task.
    :param func: the function to callback from the decorator
    :return: either the function call or raises an PermissionDenied
    """

    def wrapper(request, *args, **kwargs):

        if not base_check(request):
            return redirect(
                '{0}?next={1}'.format(
                    reverse('core_login'),
                    request.path_info
                )
            )

        elif request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)

        # User is Assigned as proofreader, regardless of role
        elif models.GalleyProofing.objects.filter(
                pk=kwargs['assignment_id'],
                proofreader=request.user,
                cancelled=False,
                completed__isnull=True,
                round__article__journal=request.journal
        ).exists():
            return func(request, *args, **kwargs)

        else:
            deny_access(request)

    return wrapper

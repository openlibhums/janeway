__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import Http404


def screener_for_assignment_required(func):
    """Allow only the screener assigned to a given ScreeningAssignment to
    proceed. Returns 404 to anonymous or other users so the assignment's
    existence is not leaked.
    """

    @login_required
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        from screening import models as screening_models

        assignment_id = kwargs.get("assignment_id")
        assignment = screening_models.ScreeningAssignment.objects.filter(
            pk=assignment_id,
            article__journal=request.journal,
        ).first()
        if assignment is None or assignment.screener != request.user:
            raise Http404
        kwargs["assignment"] = assignment
        return func(request, *args, **kwargs)

    return wrapper


def screener_or_editor_for_assignment_required(func):
    """Permit either the named screener or any journal editor / staff to
    access a ScreeningAssignment-scoped view. Used for the form-filling
    and confirmation pages where editors may need to act on the
    screener's behalf.
    """

    @login_required
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        from screening import models as screening_models

        assignment_id = kwargs.get("assignment_id")
        assignment = screening_models.ScreeningAssignment.objects.filter(
            pk=assignment_id,
            article__journal=request.journal,
        ).first()
        if assignment is None:
            raise Http404
        is_screener = assignment.screener == request.user
        is_editor = (
            request.user.is_staff
            or request.user.is_editor(request)
            or request.user.is_section_editor(request)
        )
        if not (is_screener or is_editor):
            raise Http404
        kwargs["assignment"] = assignment
        return func(request, *args, **kwargs)

    return wrapper

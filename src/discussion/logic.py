__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.http import Http404
from django.shortcuts import get_object_or_404

from discussion import models


def user_can_manage_discussions(user, journal=None, repository=None):
    """
    Canonical check for who can manage discussion threads.

    Journal editors, journal managers and staff manage a journal's threads;
    repository managers and staff manage a repository's threads. Outside any
    tenant only staff qualify.
    """
    if not user or not user.is_authenticated:
        return False
    if journal:
        return user.check_role(journal, "editor")
    if repository:
        return user.is_staff or repository.managers.filter(pk=user.pk).exists()
    return user.is_staff


def get_thread_or_404(request, thread_id, article_id=None, preprint_id=None):
    """
    Fetch a thread scoped to the requesting tenant.

    In a journal context only threads on that journal's articles resolve; in
    a repository context only threads on that repository's preprints. Outside
    any tenant, staff may fetch any thread. Passing article_id or preprint_id
    additionally pins the thread to the object named in the URL.
    """
    lookup = {"pk": thread_id}
    if article_id:
        lookup["article_id"] = article_id
    if preprint_id:
        lookup["preprint_id"] = preprint_id
    if request.journal:
        lookup["article__journal"] = request.journal
    elif request.repository:
        lookup["preprint__repository"] = request.repository
    elif not request.user.is_staff:
        raise Http404
    return get_object_or_404(models.Thread, **lookup)

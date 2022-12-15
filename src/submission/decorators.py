from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from submission import models


def submission_is_enabled(func):
    """ This decorator checks that a user is a reviewer, Note that this decorator does NOT check for conflict of
    interest problems. Use the article_editor_user_required decorator (not yet written) to do a check against an
    article.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def submission_is_enabled_wrapper(request, *args, **kwargs):
        if not request.journal:
            raise PermissionDenied(
                _('This page can only be accessed on Journals.'),
            )

        if request.journal.get_setting(
                'general',
                'disable_journal_submission',
        ) and not request.user.is_staff:
            raise PermissionDenied(
                _('Submission is disabled for this journal.'),
            )

        return func(request, *args, **kwargs)

    return submission_is_enabled_wrapper


def funding_is_enabled(func):
    """ Test if funding is enabled before returning the wrapped view

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """
    @wraps(func)
    def funding_is_enabled(request, *args, **kwargs):
        if "article_id" in kwargs:
            article_id = kwargs['article_id']
            article = models.Article.get_article(
                request.journal, 'id', article_id)

            # Staff and editors can bypass this requirement.
            if (
                request.user.is_staff
                or request.user in article.section_editors()
                or request.user.is_editor(
                    request=None,
                    journal=article.journal,
                )
            ):
                return func(request, *args, **kwargs)

        configuration = request.journal.submissionconfiguration
        if not configuration.funding:
            raise Http404

        return func(request, *args, **kwargs)

    return funding_is_enabled

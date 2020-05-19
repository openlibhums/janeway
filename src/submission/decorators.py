from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _


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
        ):
            raise PermissionDenied(
                _('Submission is disabled for this journal.'),
            )

        return func(request, *args, **kwargs)

    return submission_is_enabled_wrapper


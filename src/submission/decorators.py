from django.http import Http404

from utils import setting_handler


def submission_is_enabled(func):
    """ This decorator checks that a user is a reviewer, Note that this decorator does NOT check for conflict of
    interest problems. Use the article_editor_user_required decorator (not yet written) to do a check against an
    article.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):

        submission_disabled = setting_handler.get_setting('general', 'disable_journal_submission', request.journal)

        if submission_disabled.processed_value and not request.user.is_staff:
            raise Http404()
        else:
            return func(request, *args, **kwargs)

    return wrapper

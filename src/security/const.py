from django.utils.translation import gettext_lazy as _

from utils.const import EnumContains


class AccessDeniedMessages(EnumContains):
    """Explanations shown to a reader who has been denied access."""

    SIGN_IN_REQUIRED = _("You need to sign in to view this page.")

    # Shown when a page needed a role the account does not hold.
    WRONG_ACCOUNT_ADVICE = _(
        "If you have more than one account, sign out and sign in again with "
        "the correct account."
    )

    # Shown when a task link was opened by the wrong account.
    TASK_INVITATION_ADVICE = _(
        "If you have more than one account, sign out and sign in again using "
        "the email address that received the task invitation."
    )

    # These describe the account making the request and never the account
    # the task belongs to, so that the page cannot be used to discover who
    # is working on what.
    REVIEW_NOT_ASSIGNED = _("This review is not assigned to %(email)s.")
    COPYEDIT_NOT_ASSIGNED = _("This copyediting task is not assigned to %(email)s.")
    PROOFING_NOT_ASSIGNED = _("This proofing task is not assigned to %(email)s.")
    TYPESETTING_NOT_ASSIGNED = _("This typesetting task is not assigned to %(email)s.")
    ARTICLE_NOT_ASSOCIATED = _(
        "This article is not associated with the account %(email)s."
    )

    REVIEW_LINK_INVALID = _(
        "This review link is no longer valid. Ask the editor who invited you "
        "to send a new invitation."
    )
    REVIEW_STAGE_PASSED = _(
        "This article has moved past the review stage, so the review is now "
        "closed. You do not need to do anything further. Contact the editor "
        "if you were expecting to complete this review."
    )
    TASK_CANCELLED = _("This task was cancelled, so there is nothing left to do.")
    TASK_COMPLETED = _("You have already completed this task.")

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.utils.translation import gettext as _

from production import models as production_models
from proofing import models as proofing_models
from security.const import AccessDeniedMessages as ADM
from submission import models as submission_models
from utils import setting_handler


def task_not_assigned_message(user, message):
    """Explains that a task belongs to a different account.

    Deliberately says nothing about who the task does belong to, whether it
    sits on another journal, or whether it exists at all, so that the message
    cannot be used to discover any of those.

    :param user: the Account making the request
    :param message: an AccessDeniedMessages member accepting an email
    """
    if not getattr(user, "is_authenticated", False):
        return str(ADM.SIGN_IN_REQUIRED.value)

    return " ".join(
        [
            str(message.value) % {"email": user.email},
            str(ADM.TASK_INVITATION_ADVICE.value),
        ]
    )


def access_denied_message(user, roles, required_roles=None, journal=None):
    """Builds the explanation shown to a user who has been denied access.

    Only ever describes the account making the request, never the account a
    task belongs to, so that the page cannot be used to discover who is
    working on what.

    The roles a reader holds are recorded per journal, so that part of the
    message is left out entirely on press and repository pages rather than
    describing a journal the reader is not looking at.

    :param user: the Account making the request, or an anonymous user
    :param roles: the AccountRoles the account holds on this journal
    :param required_roles: names of the roles the page asks for, if known
    :param journal: the journal in scope, if the request has one
    """
    if not getattr(user, "is_authenticated", False):
        return str(ADM.SIGN_IN_REQUIRED.value)

    parts = [_("You are signed in as %(email)s.") % {"email": user.email}]

    if journal:
        role_names = sorted({role.role.name for role in roles})
        if role_names:
            parts.append(
                _("On this journal your account has these roles: %(roles)s.")
                % {"roles": ", ".join(role_names)}
            )
        else:
            parts.append(_("Your account has no roles on this journal."))

    if required_roles:
        parts.append(
            _("This page is for users with the %(required)s role.")
            % {"required": " or ".join(sorted(str(role) for role in required_roles))}
        )

    parts.append(ADM.WRONG_ACCOUNT_ADVICE.value)
    return " ".join(str(part) for part in parts)


def can_edit_file(request, user, file_object, article):
    if user.is_anonymous:
        return False

    # a general set of conditions that allow file editing
    if user.is_staff or user.is_editor(request) or file_object.owner == user:
        return True

    # allow section editors to edit files of articles assigned to them
    if user.is_section_editor(request) and user in article.section_editors():
        return True

    # allow file editing when the user is a production manager and the piece is in production
    try:
        production_assigned = production_models.ProductionAssignment.objects.get(
            article=article,
        )

        if (
            (
                user.is_production(request)
                and production_assigned.production_manager.pk == user.pk
            )
            and article.stage == submission_models.STAGE_TYPESETTING
            and file_object.is_galley
        ):
            return True
    except production_models.ProductionAssignment.DoesNotExist:
        pass

    # allow file editing when the user is the proofing manager for this article
    try:
        proofing_models.ProofingAssignment.objects.get(
            proofing_manager=user, article=file_object.article
        )
        return True
    except proofing_models.ProofingAssignment.DoesNotExist:
        pass

    # Allow access to typesetters in production
    prod_task = production_models.TypesetTask.objects.filter(
        typesetter=request.user, assignment__article=article, completed__isnull=True
    ).exists()
    if prod_task:
        return True

    # Allow access to typesetters during proofing corrections
    correction_task = proofing_models.TypesetterProofingTask.objects.filter(
        typesetter=request.user,
        proofing_task__round__assignment__article=article,
        completed__isnull=True,
    )

    if correction_task:
        return True

    # deny access to all others
    return False


def can_view_file_history(request, user, file_object, article_object):
    # for now, delegate entirely to can_edit_file. This method is left here for finer grained specificity if needed
    # at a later date

    # TODO: if this is ever changed, then tests need to be written for the decorator file_history_user_required
    return can_edit_file(request, user, file_object, article_object)


def can_view_file(request, user, file_object=None):
    if not file_object:
        return True
    # general conditions under which a file can be viewed
    if file_object.privacy == "public":
        return True

    if user.is_anonymous:
        return False

    if user.is_staff or user.is_editor(request) or file_object.owner == user:
        return True

    # allow section editors to view files of articles assigned to them
    if user.is_section_editor(request) and file_object.article:
        if user in file_object.article.section_editors():
            return True

    # allow file editing when the user is the proofing manager for this article
    try:
        proofing_models.ProofingAssignment.objects.get(
            proofing_manager=user,
            article__pk=file_object.article_id,
            completed__isnull=True,
        )
        return True
    except proofing_models.ProofingAssignment.DoesNotExist:
        pass

    if file_object.article_id:
        if proofing_models.TypesetterProofingTask.objects.filter(
            proofing_task__round__assignment__article__pk=file_object.article_id,
            typesetter=request.user,
            completed__isnull=True,
        ).exists():
            return True

    try:
        production_assigned = production_models.ProductionAssignment.objects.get(
            article=file_object.article
        )
        typeset_assignments = production_assigned.active_typeset_tasks()
        typesetters = [task.typesetter for task in typeset_assignments]

        if request.user in typesetters:
            return True
    except production_models.ProductionAssignment.DoesNotExist:
        pass

    # deny access to all others
    return False


def is_data_figure_file(file_object, article_object):
    # general check that the file is a data or figure file in the article
    if article_object.data_figure_files.filter(pk=file_object.pk).exists():
        return True

    # deny access to all others
    return False


def can_see_pii(request, article):
    # Before doing anything, check the setting is enabled:
    se_pii_filter_enabled = setting_handler.get_setting(
        setting_group_name="permission",
        setting_name="se_pii_filter",
        journal=article.journal,
    ).processed_value

    # early return if filter not enabled
    if not se_pii_filter_enabled:
        return True

    # Check if the user is an SE and return an anonymised value.
    # If the user is not a section editor we assume they have permission
    # to view the actual value.
    stages = [
        submission_models.STAGE_UNASSIGNED,
        submission_models.STAGE_ASSIGNED,
        submission_models.STAGE_UNDER_REVIEW,
        submission_models.STAGE_UNDER_REVISION,
    ]
    if request.user in article.section_editors() and article.stage in stages:
        return False
    return True

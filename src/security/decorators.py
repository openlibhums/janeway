__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import messages
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from core import models as core_models
from review import models as review_models
from production import models as production_models
from submission import models
from copyediting import models as copyediting_models
from proofing import models as proofing_models
from security.logic import can_edit_file, can_view_file_history, can_view_file, is_data_figure_file
from utils import setting_handler


# General role-based security decorators

def base_check(request):
    if request is None or request.user is None:
        return False

    if request.user.is_anonymous() or not request.user.is_active:
        return False

    return True


def editor_is_not_author(func):
    """
    This decorator confirms that the current user is not an author on an article. Can only be used where there is a
    article_id keyword arg.
    :param func: the function to callback from the decorator
    :return: the function call or a permission denied
    """

    def wrapper(request, *args, **kwargs):
        article_id = kwargs.get('article_id', None)

        if not article_id:
            raise Http404

        article = get_object_or_404(models.Article, pk=article_id)

        if request.user in article.authors.all() and not article.editor_override(request.user):
            return redirect(reverse('review_warning', kwargs={'article_id': article.pk}))

        return func(request, *args, **kwargs)

    return wrapper


def senior_editor_user_required(func):
    """ This decorator checks that a user is an editor, Note that this decorator does NOT check for conflict of interest
    problems. Use the article_editor_user_required decorator (not yet written) to do a check against an article.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):

        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)

        else:
            raise PermissionDenied

    return wrapper


def editor_user_required(func):
    """ This decorator checks that a user is an editor, Note that this decorator does NOT check for conflict of interest
    problems. Use the article_editor_user_required decorator (not yet written) to do a check against an article.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):

        article_id = kwargs.get('article_id', None)

        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)

        elif request.user.is_section_editor(request) and article_id:
            article = get_object_or_404(models.Article, pk=article_id)
            if request.user in article.section_editors():
                return func(request, *args, **kwargs)
            else:
                raise PermissionDenied("You are not a section editor for this article")

        else:
            raise PermissionDenied

    return wrapper


def section_editor_draft_decisions(func):
    """This decorator will check if: the user is a section editor and deny them access if draft decisions
    is enabled on the given journal.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an permissiondenied.
    """
    def wrapper(request, *args, **kwargs):
        article_id = kwargs.get('article_id', None)
        drafting = setting_handler.get_setting('general', 'draft_decisions', request.journal).value

        if request is None or request.user is None:
            raise PermissionDenied

        if request.user.is_section_editor(request) and article_id:
            article = get_object_or_404(models.Article, pk=article_id)
            if request.user in article.section_editors() and drafting:
                raise PermissionDenied

        return func(request, *args, **kwargs)

    return wrapper


def reviewer_user_required(func):
    """ This decorator checks that a user is a reviewer, Note that this decorator does NOT check for conflict of
    interest problems. Use the article_editor_user_required decorator (not yet written) to do a check against an
    article.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):

        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_reviewer(request) or request.user.is_staff:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def author_user_required(func):
    """ This decorator checks that a user is an author

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_author(request) or request.user.is_staff:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def article_author_required(func):
    """ This decorator checks that a user is an author and is an author of the article

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        article_id = kwargs['article_id']
        article = models.Article.get_article(request.journal, 'id', article_id)

        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_author(request) and article.user_is_author(request.user):
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def proofreader_user_required(func):
    """ This decorator checks that a user is a proofreader

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_proofreader(request) or request.user.is_proofreader(request):
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def copyeditor_user_required(func):
    """ This decorator checks that a user is a copyeditor.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_copyeditor(request) or request.user.is_copyeditor(request):
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def copyeditor_for_copyedit_required(func):
    """ This decorator checks that a user is a copyeditor and that they are the copyeditor for this article.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        copyedit_id = kwargs['copyedit_id']
        copyedit = get_object_or_404(copyediting_models.CopyeditAssignment, pk=copyedit_id)

        if request.user == copyedit.copyeditor and request.user.is_copyeditor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def typesetting_user_or_production_user_or_editor_required(func):
    """ This decorator checks that a user is a production manager

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http403
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_typesetter(request) or request.user.is_production(request) or \
                request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def production_user_or_editor_required(func):
    """ This decorator checks that a user is a production manager

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http403
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_production(request) or request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def reviewer_user_for_assignment_required(func):
    """ This decorator checks permissions for a user to accept or decline a review request. It also checks that the
    associated article is in a stage for which it is valid to perform this action.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        from review import logic as reviewer_logic

        access_code = reviewer_logic.get_access_code(request)
        assignment_id = kwargs['assignment_id']

        if not access_code and not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if access_code is not None:
            try:
                assignment = review_models.ReviewAssignment.objects.get(pk=assignment_id,
                                                                        access_code=access_code)

                if assignment:
                    return func(request, *args, **kwargs)
                else:
                    raise PermissionDenied

            except review_models.ReviewAssignment.DoesNotExist:
                raise PermissionDenied

        if request.user.is_anonymous() or not request.user.is_active:
            raise PermissionDenied

        if not request.user.is_reviewer(request):
            raise PermissionDenied

        try:
            if request.user.is_staff:
                assignment = review_models.ReviewAssignment.objects.get(pk=assignment_id)

                if assignment:
                    return func(request, *args, **kwargs)
                else:
                    raise PermissionDenied

            assignment = review_models.ReviewAssignment.objects.get(pk=assignment_id, reviewer=request.user)

            if assignment:

                if assignment.article.stage != models.STAGE_ASSIGNED \
                        and assignment.article.stage != models.STAGE_UNDER_REVIEW:
                    raise PermissionDenied
                else:
                    return func(request, *args, **kwargs)
            else:
                raise PermissionDenied
        except review_models.ReviewAssignment.DoesNotExist:
            raise PermissionDenied

    return wrapper


# Article-specific user enforcement
def article_production_user_required(func):
    """ This decorator checks permissions for a user to view production information about a specific article

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        article_id = kwargs['article_id']

        article = models.Article.get_article(request.journal, 'id', article_id)
        assigned = get_object_or_404(production_models.ProductionAssignment, article=article)

        # If article is in production and user is the production manager
        if ((request.user.is_production(request) and assigned.production_manager.pk == request.user.pk) and article.stage == models.STAGE_TYPESETTING) or request.user.is_staff:
            return func(request, *args, **kwargs)

        # If article is in proofing and the user is the proofing manager
        if article.stage == models.STAGE_PROOFING:
            proofing_assigned = get_object_or_404(proofing_models.ProofingAssignment, article=article)
            if (request.user.is_proofing_manager and proofing_assigned.proofing_manager == request.user) or \
                    request.user.is_staff:
                return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def article_stage_production_required(func):
    """ This decorator checks that a specific article is in the typesetting stage

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        article_id = kwargs['article_id']

        article = models.Article.get_article(request.journal, 'id', article_id)

        if article and article.stage == models.STAGE_TYPESETTING:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def article_stage_accepted_or_later_required(func):
    """ This decorator checks that a specific article has been accepted

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        identifier_type = kwargs['identifier_type']
        identifier = kwargs['identifier']

        article_object = models.Article.get_article(request.journal, identifier_type, identifier)

        if article_object is None or not article_object.is_accepted():
            raise PermissionDenied
        else:
            return func(request, *args, **kwargs)

    return wrapper


def article_stage_accepted_or_later_or_staff_required(func):
    """ This decorator checks that a specific article has been accepted or the user is staff

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        identifier_type = kwargs['identifier_type']
        identifier = kwargs['identifier']

        article_object = models.Article.get_article(request.journal, identifier_type, identifier)

        if article_object is not None and article_object.is_accepted():
            return func(request, *args, **kwargs)
        elif request.user.is_anonymous():
            raise PermissionDenied
        elif article_object is not None and (request.user.is_editor(request) or request.user.is_staff):
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def article_edit_user_required(func):
    """ This decorator checks permissions for a user to edit a specific article

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        article_id = kwargs['article_id']

        article = models.Article.get_article(request.journal, 'id', article_id)

        if article.can_edit(request.user):
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


# File permissions

def file_user_required(func):
    """ This decorator checks that a user has permission to view a file

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        file_id = kwargs['file_id']

        if file_id == "None":
            return func(request, *args, **kwargs)

        file_object = get_object_or_404(core_models.File, pk=file_id)

        if can_view_file(request, request.user, file_object):
            return func(request, *args, **kwargs)
        else:
            messages.add_message(request, messages.ERROR, 'File is not accessible to this user.')
            raise PermissionDenied

    return wrapper


def file_history_user_required(func):
    """ This decorator checks permissions for a user to view the history of a specific article

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        file_object = get_object_or_404(core_models.File, pk=kwargs['file_id'])

        try:
            article = models.Article.get_article(request.journal, 'id', kwargs['article_id'])
        except KeyError:
            article = models.Article.get_article(request.journal, kwargs['identifier_type'], kwargs['identifier'])

        if can_view_file_history(request, request.user, file_object, article):
            return func(request, *args, **kwargs)

        messages.add_message(request, messages.ERROR, 'File editing not accessible to this user.')
        raise PermissionDenied

    return wrapper


def file_edit_user_required(func):
    """ This decorator checks permissions for a user to edit a specific article

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        file_object = get_object_or_404(core_models.File, pk=kwargs['file_id'])

        try:
            article = models.Article.get_article(request.journal, 'id', kwargs['article_id'])
        except KeyError:
            article = models.Article.get_article(request.journal, kwargs['identifier_type'], kwargs['identifier'])

        if can_edit_file(request, request.user, file_object, article):
            return func(request, *args, **kwargs)

        messages.add_message(request, messages.ERROR, 'File editing not accessible to this user.')
        raise PermissionDenied

    return wrapper


def data_figure_file(func):
    """ This decorator checks that a file is a data or figure file in the specified article

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        file_object = get_object_or_404(core_models.File, pk=kwargs['file_id'])

        try:
            article = models.Article.get_article(request.journal, 'id', kwargs['article_id'])
        except KeyError:
            article = models.Article.get_article(request.journal, kwargs['identifier_type'], kwargs['identifier'])

        if is_data_figure_file(file_object, article):
            return func(request, *args, **kwargs)

        messages.add_message(request, messages.ERROR, 'File is not a data or figure file.')
        raise PermissionDenied

    return wrapper


# General checks to avoid "raise Http404()" logic elsewhere

def has_request(func):
    """ This decorator checks that the request object is not None

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        if request is not None:
            return func(request, *args, **kwargs)
        else:
            raise Http404()

    return wrapper


def has_journal(func):
    """ This decorator checks that the request object is not None

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        if request.journal is not None:
            return func(request, *args, **kwargs)
        else:
            raise Http404()

    return wrapper


def article_exists(func):
    """ This decorator checks that a specific article has been accepted or the user is staff

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        try:
            article_object = models.Article.get_article(request.journal, 'id', kwargs['article_id'])
        except KeyError:
            article_object = models.Article.get_article(request.journal,
                                                        kwargs['identifier_type'],
                                                        kwargs['identifier'])

        if article_object is None:
            raise Http404()
        else:
            return func(request, *args, **kwargs)

    return wrapper


def article_decision_not_made(func):
    """
    This decorator pulls a review and checks if it is accepted or declined. Raises a permission error if
    a decision has already been made.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an PermissionDenied
    """

    def wrapper(request, *args, **kwargs):
        try:
            article_object = models.Article.objects.get(pk=kwargs['article_id'], journal=request.journal)
        except KeyError:
            article_object = review_models.ReviewAssignment.objects.get(pk=kwargs['review_id'],
                                                                        article__journal=request.journal).article

        if article_object.stage == models.STAGE_ASSIGNED or article_object.stage == models.STAGE_UNDER_REVIEW\
                or article_object.stage == models.STAGE_UNDER_REVISION:
            return func(request, *args, **kwargs)
        else:
            messages.add_message(request, messages.WARNING, 'This article has already been accepted or declined.')
            return redirect(reverse('review_in_review', kwargs={'article_id': article_object.pk}))

    return wrapper


def typesetter_user_required(func):
    """ This decorator checks that a user is a typesetter.

    :param func: the function to callback from the decorator
    :return: either the function call or raises an Http404
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_typesetter(request) or request.user.is_staff:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def typesetter_or_editor_required(func):
    """
        This decorator pulls a typeset task and checks the current user is either an editor or a typesetter with
        an active task.

        :param func: the function to callback from the decorator
        :return: either the function call or raises an PermissionDenied
        """

    def wrapper(request, *args, **kwargs):
        typeset_id = kwargs.get('typeset_id', None)

        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)

        typeset_assignment = get_object_or_404(production_models.TypesetTask, pk=typeset_id)
        if request.user == typeset_assignment.typesetter and not typeset_assignment.completed and \
                request.user.is_typesetter(request):
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def proofing_manager_or_editor_required(func):
    """
    This decorator checks if the user is an editor and passes them through, or checks if the user is a proofing manager.
    :param func: the function to callback from the decorator
    :return: either the function call or raises an PermissionDenied
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_editor(request) or request.user.is_staff or request.user.is_proofing_manager(request):
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper


def proofing_manager_for_article_required(func):
    """
    Checks that the user is an editor or is a proofing manager for the current article.
    :param func: the function to callback from the decorator
    :return: either the function call or raises an PermissionDenied
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        article = get_object_or_404(models.Article, pk=kwargs['article_id'])

        if not hasattr(article, 'proofingassignment'):
            return redirect(reverse('proofing_list'))

        if request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)

        if not request.user.is_proofing_manager(request):
            raise PermissionDenied

        try:
            proofing_models.ProofingAssignment.objects.get(
                article=article,
                proofing_manager=request.user
            )
            return func(request, *args, **kwargs)
        except proofing_models.ProofingAssignment.DoesNotExist:
            raise PermissionDenied

    return wrapper


def proofreader_or_typesetter_required(func):
    """
    Checks if the user is a proofreader or typesetter
    :param func: the function to callback from the decorator
    :return: either the function call or raises an PermissionDenied:
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)

        if request.user.is_proofreader(request) or request.user.is_typesetter(request):
            return func(request, *args, **kwargs)

        raise PermissionDenied

    return wrapper


def proofreader_for_article_required(func):
    """
    Checks that the current user is the proofreader for the current task.
    :param func: the function to callback from the decorator
    :return: either the function call or raises an PermissionDenied
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)

        if not request.user.is_proofreader(request):
            raise PermissionDenied

        if kwargs.get('article_id', None):
            article = get_object_or_404(models.Article, pk=kwargs['article_id'], journal=request.journal)
            if request.user == article.proofingassignment.proofing_manager:
                return func(request, *args, **kwargs)

        try:
            proofing_models.ProofingTask.objects.get(pk=kwargs['proofing_task_id'],
                                                     proofreader=request.user,
                                                     cancelled=False,
                                                     completed__isnull=True,
                                                     round__assignment__article__journal=request.journal)
            return func(request, *args, **kwargs)
        except proofing_models.ProofingTask.DoesNotExist:
            raise PermissionDenied

    return wrapper


def typesetter_for_corrections_required(func):
    """
    Checks that the current user is the typesetter for the current task.
    :param func: the function to callback from the decorator
    :return: either the function call or raises an PermissionDenied
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user.is_editor(request) or request.user.is_staff:
            return func(request, *args, **kwargs)

        try:
            proofing_models.TypesetterProofingTask.objects.get(
                pk=kwargs['typeset_task_id'],
                cancelled=False,
                completed__isnull=True,
                typesetter=request.user,
                proofing_task__round__assignment__article__journal=request.journal)
            return func(request, *args, **kwargs)
        except proofing_models.TypesetterProofingTask.DoesNotExist:
            raise PermissionDenied
    return wrapper


def press_only(func):
    """
    Checks that there is no journal object.
    :param func: the function to callback from the decorator
    :return: either the function call or a redirect
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))
        if request.journal:
            return redirect(reverse('core_manager'))

        return func(request, *args, **kwargs)

    return wrapper


def preprint_editor_or_author_required(func):
    """
    Checks that the current user is either a preprint editor or is an author for the current paper
    :param func:
    :return:
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        article = get_object_or_404(models.Article.preprints, pk=kwargs['article_id'])

        if request.user in article.authors.all() or request.user.is_staff:
            return func(request, *args, **kwargs)

        if request.user in article.subject_editors():
            return func(request, *args, **kwargs)

        raise PermissionDenied

    return wrapper


def is_article_preprint_editor(func):
    """
    Checks that the current user is a preprint editor for the current paper
    :param func:
    :return:
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        article = get_object_or_404(models.Article.preprints, pk=kwargs['article_id'])

        if request.user in article.subject_editors() or request.user.is_staff:
            return func(request, *args, **kwargs)

        raise PermissionDenied

    return wrapper


def is_preprint_editor(func):
    """
    Checks that the current user is a preprint editor
    :param func:
    :return:
    """

    def wrapper(request, *args, **kwargs):
        if not base_check(request):
            return redirect('{0}?next={1}'.format(reverse('core_login'), request.path))

        if request.user in request.press.preprint_editors() or request.user.is_staff:
            return func(request, *args, **kwargs)

        raise PermissionDenied

    return wrapper

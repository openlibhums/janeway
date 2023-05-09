__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from production import models as production_models
from proofing import models as proofing_models
from submission import models as submission_models


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
        production_assigned = production_models.ProductionAssignment.objects.get(article=article,)

        if (user.is_production(request) and production_assigned.production_manager.pk == user.pk) and \
                article.stage == submission_models.STAGE_TYPESETTING and file_object.is_galley:
            return True
    except production_models.ProductionAssignment.DoesNotExist:
        pass

    # allow file editing when the user is the proofing manager for this article
    try:
        proofing_models.ProofingAssignment.objects.get(proofing_manager=user,
                                                       article=file_object.article)
        return True
    except proofing_models.ProofingAssignment.DoesNotExist:
        pass

    # Allow access to typesetters in production
    prod_task = production_models.TypesetTask.objects.filter(
        typesetter=request.user,
        assignment__article=article,
        completed__isnull=True
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
    if file_object.privacy == 'public':
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
        proofing_models.ProofingAssignment.objects.get(proofing_manager=user,
                                                       article__pk=file_object.article_id,
                                                       completed__isnull=True)
        return True
    except proofing_models.ProofingAssignment.DoesNotExist:
        pass

    if file_object.article_id:
        if proofing_models.TypesetterProofingTask.objects.filter(
                proofing_task__round__assignment__article__pk=file_object.article_id,
                typesetter=request.user,
                completed__isnull=True
        ).exists():
            return True

    try:
        production_assigned = production_models.ProductionAssignment.objects.get(article=file_object.article)
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

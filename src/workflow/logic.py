from submission import models as submissions_models
from proofing import models as proofing_models
from production import models as production_models
from journal import models as journal_models
from core import models as core_models
from utils.shared import clear_cache


def reopen_proofing_assignments(article):
    """
    Finds and marks proofing assignments as open for a given article.
    :param article: Article object
    :return: None
    """
    for assignment in proofing_models.ProofingAssignment.objects.filter(
        article=article,
    ):
        assignment.completed = None
        assignment.save()


def reopen_production_assignments(article):
    """
    Finds and marks production assignments as open for a given article.
    :param article: Article objects
    :return: None
    """
    for assignment in production_models.ProductionAssignment.objects.filter(
        article=article,
    ):
        assignment.closed = None
        assignment.accepted_by_manager = None
        assignment.save()


def reset_prepub_checklist(article):
    """
    Resets all prepub checklist items for a given article.
    :param article: Article object
    :return: None
    """
    for item in journal_models.PrePublicationChecklistItem.objects.filter(
        article=article,
    ):
        item.completed = False
        item.completed_by = None
        item.completed_on = None
        item.save()


def drop_workflow_log_entries(article, stages_to_process):
    """
    Finds and deletes workflow log entries for stages being processed.
    :param article: Article object
    :param stages_to_process: A List of stage names
    :return: None
    """
    *stages_to_delete, new_current_stage = stages_to_process
    entries = core_models.WorkflowLog.objects.filter(
        article=article,
        element__stage__in=stages_to_delete,
    )
    entries.delete()

    return stages_to_delete


def stages_in_between(from_stage, to_stage, article):
    """
    Works out the stages an article has been in between the two given stages.
    :param from_stage: stage name, string
    :param to_stage: stage_name, string
    :param article: Article object
    :return: list of stages in reverse order
    """
    stages = [log.element.stage for log in article.workflow_stages().reverse()]
    stage_index = stages.index(to_stage)

    return stages[:stage_index+1]


def move_to_stage(from_stage, to_stage, article):
    stages_to_process = stages_in_between(from_stage, to_stage, article)

    for stage in stages_to_process:
        if stage == submissions_models.STAGE_READY_FOR_PUBLICATION:
            article.date_published = None
            article.stage = submissions_models.STAGE_READY_FOR_PUBLICATION
            reset_prepub_checklist(article)

        elif stage == submissions_models.STAGE_PROOFING:
            article.stage = submissions_models.STAGE_PROOFING
            reopen_proofing_assignments(article)

        elif stage == submissions_models.STAGE_TYPESETTING:
            article.stage = submissions_models.STAGE_TYPESETTING
            reopen_production_assignments(article)

        elif stage == submissions_models.STAGE_EDITOR_COPYEDITING:
            article.stage = submissions_models.STAGE_EDITOR_COPYEDITING

        elif stage == submissions_models.STAGE_UNASSIGNED:
            article.stage = submissions_models.STAGE_UNDER_REVIEW
            article.date_accepted = None
            article.date_declined = None

        else:
            pass
            # TODO: No stage found, likely a plugin, find it?

    article.save()
    stages_to_delete = drop_workflow_log_entries(article, stages_to_process)
    clear_cache()

    return stages_to_delete

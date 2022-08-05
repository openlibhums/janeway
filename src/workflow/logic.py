from submission import models as submissions_models
from proofing import models as proofing_models
from production import models as production_models
from journal import models as journal_models
from core import models as core_models, workflow as core_workflow, plugin_loader
from utils.shared import clear_cache
from importlib import import_module
from utils import logger

logger = logger.get_logger(__name__)


def stage_element_translator(directory="plugins", prefix="plugins", permissive=False):
    """
    Rudimentary loader of plugin workflow pairings.
    """

    dirs = plugin_loader.get_dirs(directory)
    for dir in dirs:
        plugin = plugin_loader.get_plugin(dir, permissive)
        if plugin:
            module_name = "{0}.{1}.plugin_settings".format(prefix, dir)
            plugin_settings = import_module(module_name)

            workflow_check = plugin_loader.check_plugin_workflow(plugin_settings)
            if workflow_check:
                core_workflow.ELEMENT_STAGES[
                    plugin_settings.PLUGIN_NAME] = [plugin_settings.STAGE]
                core_workflow.STAGES_ELEMENTS[
                    plugin_settings.STAGE] = plugin_settings.PLUGIN_NAME

    return core_workflow.STAGES_ELEMENTS, core_workflow.ELEMENT_STAGES

STAGES_ELEMENTS, ELEMENT_STAGES = stage_element_translator()

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
    DEPRECATED
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
    Or, if stage_to is beyond current stage, works out what stages an article
    would go through to get there, given the journal's current workflow.
    :param from_stage: stage name, string
    :param to_stage: stage_name, string
    :param article: Article object
    :return: list of stages, in reverse order if moving back
    """
    if stage_is_before_stage(to_stage, from_stage, article.journal):
        # Travelling to the past
        stages = []
        for element in article.journal.workflow().elements.all().reverse():
            element_stages = ELEMENT_STAGES[element.element_name]
            stages += reversed(list(element_stages))
    else:
        # Travelling to the future
        stages = []
        for element in article.journal.workflow().elements.all():
            stages += ELEMENT_STAGES[element.element_name]

    # Normalize from and to stages
    from_stage_index = stages.index(from_stage)
    to_stage_index = stages.index(to_stage)
    return stages[from_stage_index:to_stage_index+1]


def stage_is_before_stage(stage_a, stage_b, journal):
    """
    Compares the order of the workflow elements
    that correspond to the stages passed.
    :param stage_a: stage name, string
    :param stage_b: stage_name, string
    :return: True, False, or None if not recognized
    """
    try:
        stages = []
        for element in journal.workflow().elements.all():
            stages += ELEMENT_STAGES[element.element_name]
        return stages.index(stage_a) < stages.index(stage_b)
    except KeyError:
        logger.warning(f'{stage_a} or {stage_b} not recognized.')

def move_to_stage(from_stage, to_stage, article):
    stages_to_process = stages_in_between(from_stage, to_stage, article)
    for stage in stages_to_process:

        # Take care of details particular to various stages
        if stage == submissions_models.STAGE_READY_FOR_PUBLICATION:
            article.date_published = None
            reset_prepub_checklist(article)

        elif stage == submissions_models.STAGE_PROOFING:
            reopen_proofing_assignments(article)

        elif stage == submissions_models.STAGE_TYPESETTING:
            reopen_production_assignments(article)

        elif stage == submissions_models.STAGE_UNASSIGNED:
            article.date_accepted = None
            article.date_declined = None

        else:
            pass
            # TODO: No stage found, likely a plugin, find it?

        # Recognize the stage
        if stage in STAGES_ELEMENTS:
            element_name = STAGES_ELEMENTS[stage]

            # Create any needed workflow log
            element = core_models.WorkflowElement.objects.get(
                journal=article.journal,
                element_name=element_name,
            )
            core_models.WorkflowLog.objects.get_or_create(
                article=article,
                element=element
            )

            if stage == to_stage:

                # Set the stage if this is the target.
                article.stage = stage

    article.save()
    clear_cache()

    return stages_to_process

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from core import models as core_models, workflow
from utils import transactional_emails, workflow_tasks
from events import logic as event_logic
from journal import logic as journal_logic
from identifiers import logic as id_logic

# wire up event notifications

from events import logic as event_logic  # We always import this as event_logic

# Submission
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_SUBMITTED,
                                      transactional_emails.send_submission_acknowledgement,
                                      workflow.workflow_auto_assign_editors)
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_ASSIGNED_ACKNOWLEDGE,
                                      transactional_emails.send_editor_assigned_acknowledgements)
event_logic.Events.register_for_event(event_logic.Events.ON_EDITOR_MANUALLY_ASSIGNED,
                                      transactional_emails.send_editor_manually_assigned)
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_UNASSIGNED,
        transactional_emails.send_editor_unassigned_notice)

# Review
event_logic.Events.register_for_event(event_logic.Events.ON_REVIEWER_REQUESTED_NOTIFICATION,
                                      transactional_emails.send_reviewer_requested)
event_logic.Events.register_for_event(event_logic.Events.ON_REVIEWER_REQUESTED_ACKNOWLEDGE,
                                      transactional_emails.send_reviewer_requested_acknowledgements)
event_logic.Events.register_for_event(event_logic.Events.ON_REVIEW_WITHDRAWL,
                                      transactional_emails.send_reviewer_withdrawl_notice)
event_logic.Events.register_for_event(event_logic.Events.ON_REVIEWER_ACCEPTED,
                                      transactional_emails.send_reviewer_accepted_or_decline_acknowledgements)
event_logic.Events.register_for_event(event_logic.Events.ON_REVIEWER_DECLINED,
                                      transactional_emails.send_reviewer_accepted_or_decline_acknowledgements)
event_logic.Events.register_for_event(event_logic.Events.ON_REVIEW_COMPLETE,
                                      transactional_emails.send_review_complete_acknowledgements)
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_DECLINED,
                                      transactional_emails.send_article_decision)
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_UNDECLINED,
                                      transactional_emails.send_article_decision)
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_ACCEPTED,
                                      transactional_emails.send_article_decision)
event_logic.Events.register_for_event(event_logic.Events.ON_DRAFT_DECISION,
                                      transactional_emails.send_draft_decison)
event_logic.Events.register_for_event(event_logic.Events.ON_DRAFT_DECISION_DECLINED,
                                      transactional_emails.send_draft_decision_declined)
event_logic.Events.register_for_event(event_logic.Events.ON_REVIEW_SECURITY_OVERRIDE,
                                      transactional_emails.review_sec_override_notification)

# Revisions
event_logic.Events.register_for_event(event_logic.Events.ON_REVISIONS_REQUESTED_NOTIFY,
                                      transactional_emails.send_revisions_request)
event_logic.Events.register_for_event(event_logic.Events.ON_REVISIONS_COMPLETE,
                                      transactional_emails.send_revisions_complete)
event_logic.Events.register_for_event(event_logic.Events.ON_REVISIONS_COMPLETE,
                                      transactional_emails.send_revisions_author_receipt)

# Copyediting
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_ASSIGNMENT,
                                      transactional_emails.send_copyedit_assignment)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_UPDATED,
                                      transactional_emails.send_copyedit_updated)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_DELETED,
                                      transactional_emails.send_copyedit_deleted)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDITOR_DECISION,
                                      transactional_emails.send_copyedit_decision)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_AUTHOR_REVIEW,
                                      transactional_emails.send_copyedit_author_review)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_AUTHOR_REVIEW_COMPLETE,
                                      transactional_emails.send_author_copyedit_complete)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_AUTHOR_REVIEW_DELETED,
                                      transactional_emails.send_author_copyedit_deleted)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_ASSIGNMENT_COMPLETE,
                                      transactional_emails.send_copyedit_complete)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_REOPEN,
                                      transactional_emails.send_copyedit_reopen)
event_logic.Events.register_for_event(event_logic.Events.ON_COPYEDIT_ACKNOWLEDGE,
                                      transactional_emails.send_copyedit_ack)

# Production
event_logic.Events.register_for_event(event_logic.Events.ON_TYPESET_TASK_ASSIGNED,
                                      transactional_emails.send_typeset_assignment)
event_logic.Events.register_for_event(event_logic.Events.ON_TYPESETTER_DECISION,
                                      transactional_emails.send_typeset_decision)
event_logic.Events.register_for_event(event_logic.Events.ON_TYPESET_TASK_DELETED,
                                      transactional_emails.send_typeset_task_deleted)
event_logic.Events.register_for_event(event_logic.Events.ON_TYPESET_COMPLETE,
                                      transactional_emails.send_typeset_complete)
event_logic.Events.register_for_event(event_logic.Events.ON_PRODUCTION_COMPLETE,
                                      transactional_emails.send_production_complete)
event_logic.Events.register_for_event(event_logic.Events.ON_PROOFING_TYPESET_CHANGES_REQUEST,
                                      transactional_emails.send_proofing_typeset_request)
event_logic.Events.register_for_event(event_logic.Events.ON_PROOFING_TYPESET_DECISION,
                                      transactional_emails.send_proofing_typeset_decision)


# Proofing
event_logic.Events.register_for_event(event_logic.Events.ON_PROOFING_MANAGER_ASSIGNMENT,
                                      transactional_emails.fire_proofing_manager_assignment)
event_logic.Events.register_for_event(event_logic.Events.ON_CANCEL_PROOFING_TASK,
                                      transactional_emails.cancel_proofing_task)
event_logic.Events.register_for_event(event_logic.Events.ON_EDIT_PROOFING_TASK,
                                      transactional_emails.edit_proofing_task)
event_logic.Events.register_for_event(event_logic.Events.ON_NOTIFY_PROOFREADER,
                                      transactional_emails.notify_proofreader)
event_logic.Events.register_for_event(event_logic.Events.ON_PROOFREADER_TASK_DECISION,
                                      transactional_emails.send_proofreader_decision)
event_logic.Events.register_for_event(event_logic.Events.ON_COMPLETE_PROOFING_TASK,
                                      transactional_emails.send_proofreader_complete_notification)
event_logic.Events.register_for_event(event_logic.Events.ON_CORRECTIONS_COMPLETE,
                                      transactional_emails.send_corrections_complete)
event_logic.Events.register_for_event(event_logic.Events.ON_PROOFING_ACK,
                                      transactional_emails.send_proofing_ack)
event_logic.Events.register_for_event(event_logic.Events.ON_PROOFING_COMPLETE,
                                      transactional_emails.send_proofing_complete)
event_logic.Events.register_for_event(event_logic.Events.ON_CORRECTIONS_CANCELLED,
                                      transactional_emails.send_cancel_corrections)

# Prepublication
event_logic.Events.register_for_event(event_logic.Events.ON_PREPUB_NOTIFICATIONS,
                                      transactional_emails.send_prepub_notifications)

# Publication
# Note: ON_AUTHOR_PUBLICATION is deprecated
event_logic.Events.register_for_event(event_logic.Events.ON_AUTHOR_PUBLICATION,
                                      transactional_emails.send_author_publication_notification)

# Send notifications to registered users.
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_SUBMITTED,
                                      journal_logic.fire_submission_notifications)
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_ACCEPTED,
                                      journal_logic.fire_acceptance_notifications)

# Preprints
event_logic.Events.register_for_event(event_logic.Events.ON_PREPRINT_SUBMISSION,
                                      transactional_emails.preprint_submission)

event_logic.Events.register_for_event(event_logic.Events.ON_PREPRINT_NOTIFICATION,
                                      transactional_emails.preprint_notification)

event_logic.Events.register_for_event(event_logic.Events.ON_PREPRINT_COMMENT,
                                      transactional_emails.preprint_comment)
event_logic.Events.register_for_event(
    event_logic.Events.ON_PREPRINT_VERSION_UPDATE,
    transactional_emails.preprint_version_update,
)

event_logic.Events.register_for_event(
    event_logic.Events.ON_ACCESS_REQUEST,
    transactional_emails.access_request_notification,
)

event_logic.Events.register_for_event(
    event_logic.Events.ON_ACCESS_REQUEST_COMPLETE,
    transactional_emails.access_request_complete,
)

event_logic.Events.register_for_event(
    event_logic.Events.ON_PREPRINT_REVIEW_NOTIFICATION,
    transactional_emails.preprint_review_notification,
)

event_logic.Events.register_for_event(
    event_logic.Events.ON_PREPRINT_REVIEW_STATUS_CHANGE,
    transactional_emails.preprint_review_status_change,
)

# wire up task-creation events
event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_SUBMITTED,
                                      workflow_tasks.assign_editors)

event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_ASSIGNED,
                                      workflow_tasks.select_reviewers)

event_logic.Events.register_for_event(event_logic.Events.ON_REVIEWER_REQUESTED,
                                      workflow_tasks.do_review_task)

event_logic.Events.register_for_event(event_logic.Events.ON_REVIEWER_ACCEPTED,
                                      workflow_tasks.perform_review_task)

event_logic.Events.register_for_event(event_logic.Events.ON_ARTICLE_ACCEPTED,
                                      workflow_tasks.create_copyedit_task)

event_logic.Events.register_for_event(event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE,
                                      workflow.workflow_element_complete)

# wire up the core task destroyer
# N.B. this is critical to the operation of the task framework. It automatically tears down tasks that have registered
# for event listeners
event_logic.Events.register_for_event('destroy_tasks', core_models.Task.destroyer)

event_logic.Events.register_for_event(
    event_logic.Events.ON_ARTICLE_ASSIGNED_TO_ISSUE,
    id_logic.on_article_assign_to_issue,
)

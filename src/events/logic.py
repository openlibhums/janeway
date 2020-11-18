__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

# we need this for strict type checking on the event destroyer
from submission import models as submission_models


class Events:
    """
    The event handling framework for Janeway
    """
    _hooks = {}

    # list of event constants used internally by Janeway

    # kwargs: article, request
    # raised when an article is submitted
    ON_ARTICLE_SUBMITTED = 'on_article_submitted'

    # kwargs: request, editor_assignment, user_message_content (will be blank), acknowledgement (false)
    # raised when an editor is assigned to an article
    ON_ARTICLE_ASSIGNED = 'on_article_assigned'
    # kwargs: request, editor_assignment, user_message_content, skip (boolean)
    # raised when an editor is unassigned from an article
    ON_ARTICLE_UNASSIGNED = 'on_article_unassigned'
    # kwargs: editor_assignment, request, user_message_content, acknowledgement (true), skip (boolean)
    # raised when an editor decides to notify the editor of the assignment (or skip the acknowledgement)
    ON_ARTICLE_ASSIGNED_ACKNOWLEDGE = 'on_article_assigned_acknowledge'

    # kwargs: review_assignment, request, user_message_content (will be blank), acknowledgement (false)
    # raised when a review is requested
    ON_REVIEWER_REQUESTED = 'on_reviewer_requested'
    # kwargs: review_assignment, request, user_message_content, acknowledgement (true), skip (boolean)
    # raised when an editor decides to notify the reviewer of the request (or skip the acknowledgement)
    ON_REVIEWER_REQUESTED_ACKNOWLEDGE = 'on_reviewer_requested_acknowledge'
    # kwargs: review_assignment, request, user_message_content, skip (boolean)
    # raised when an editor decides to notify the reviewer of a assignment withdrawl (or skip the notification)
    ON_REVIEW_WITHDRAWL = 'on_review_withdrawl'

    # kwargs: review_assignment, request, accepted (boolean)
    # raised when a reviewer accepts or declines to review
    ON_REVIEWER_ACCEPTED = 'on_reviewer_accepted'
    ON_REVIEWER_DECLINED = 'on_reviewer_declined'

    # kwargs: review_assignment, request
    # raised when a reviewer completes his or her review
    ON_REVIEW_COMPLETE = 'on_review_complete'

    # kwargs: review_assignment, request
    # raised when a reviewer completes his or her review
    ON_REVIEW_CLOSED = 'on_review_closed'

    # kwargs: article, request, user_message_content, decision, skip (boolean)
    # raised when an editor accepts or declines an article
    ON_ARTICLE_DECLINED = 'on_article_declined'

    # kwargs: article, request, user_message_content, decision, skip (boolean)
    # raised when an editor accepts or accepts an article
    ON_ARTICLE_ACCEPTED = 'on_article_accepted'

    # kwargs: article, revision, request, user_message_content, skip (boolean)
    # raised when a revision request is created
    ON_REVISIONS_REQUESTED = 'on_revisions_requested'

    # kwargs: article, revision, request, user_message_content, skip (boolean)
    # raised when a revision request notification is sent
    ON_REVISIONS_REQUESTED_NOTIFY = 'on_revisions_requested_notify'

    # kwargs: article, revision, request, skip (boolean)
    # raised when a revision request notification is sent
    ON_REVISIONS_COMPLETE = 'on_revisions_complete'

    # kwargs: article, draft, request
    # raised when a section editor adds a new draft
    ON_DRAFT_DECISION = 'on_draft_decision'

    # kwargs: article, copyeditor_assignment, request, skip (boolean)
    # raised when a copyeditor is assigned
    ON_COPYEDIT_ASSIGNMENT = 'on_copyedit_assignment'

    # kwargs: copyeditor_assignment, request, skip (boolean)
    # raised when a copyeditor assignment is updated
    ON_COPYEDIT_UPDATED = 'on_copyedit_updated'

    # kwargs: article, request
    ON_COPYEDIT_DELETED = 'on_copyedit_deleted'

    # kwargs copyeditor assignment, decision, request
    # raised when a copyeditor accepts or declines a task
    ON_COPYEDITOR_DECISION = 'on_copyeditor_decision'

    # kwargs: article, copyeditor assignment, request
    # raised when a copyedit assignment is complete
    ON_COPYEDIT_ASSIGNMENT_COMPLETE = 'on_copyedit_assignment_complete'

    # kwargs: article, copyeditor assignment, request, skip (boolean)
    # raised when an author is invited to review a copyedit
    ON_COPYEDIT_AUTHOR_REVIEW = 'on_copyedit_author_review'

    # kwargs: article, copyedit, author_review, request
    # raised when an author completes their copyedit review
    ON_COPYEDIT_AUTHOR_REVIEW_COMPLETE = 'on_copyedit_author_review_complete'

    # kwargs: article, copyeditor assignment, request, skip (boolean)
    # raised when a copyedit assignment is acknowledged
    ON_COPYEDIT_ACKNOWLEDGE = 'on_copyedit_acknowledge'

    # kwargs: article, copyeditor assignment, request, skip (boolean)
    # raised when a copyedit assignment is acknowledged
    ON_COPYEDIT_REOPEN = 'on_copyedit_reopen'

    # kwargs: article, request
    # raised when copyediting is complete
    ON_COPYEDIT_COMPLETE = 'on_copyedit_complete'

    # kwargs: production_assignment, request, skip (boolean)
    # raised when a production manager is assigned to an article
    ON_PRODUCTION_MANAGER_ASSIGNMENT = 'on_production_manager_assignment'

    # kwargs: user_content_message, typeset_task, request, skip (boolean)
    # raised when a typeset task is assigned to a typesetter
    ON_TYPESET_TASK_ASSIGNED = 'on_typeset_task_assigned'

    # kwargs: typeset_task, decision, request
    # raised when a typesetter accepts or declines a typeset task
    ON_TYPESETTER_DECISION = 'on_typesetter_decision'

    # kwargs: typeset_task, request
    # raised when an editor deletes a typesetter's task
    ON_TYPESET_TASK_DELETED = 'on_typeset_task_deleted'

    # kwargs: typeset_task, request
    # raised when a typesetter completes their task
    ON_TYPESET_COMPLETE = 'on_typeset_complete'

    # kwargs: typeset_task, request, skip(boolean)
    # raised when a typesetter is sent a second request
    ON_TYPESET_TASK_REOPENED = 'on_typeset_task_reopened'

    # kwargs: typeset_task, request, skip (boolean)
    # raised when a production manager accepts a typeset task and completed the production stage
    ON_TYPESET_ACK = 'on_typeset_ack'

    # kwargs: request, article, skip (boolean)
    # raised when a production manager completes the production stage
    ON_PRODUCTION_COMPLETE = 'on_production_complete'

    # kwargs: proofing_assignment, request, skip (boolean)
    # raised when a production manager is assigned to an article
    ON_PROOFING_MANAGER_ASSIGNMENT = 'on_proofing_manager_assignment'

    # kwargs: request, article, proofing_task, skip (boolean)
    # raised when a proofing manager invites a Proofreader
    ON_NOTIFY_PROOFREADER = 'on_notify_proofreader'

    # kwargs: request, article, proofing_task,
    # raised when a proofing manager cancels a proofing task
    ON_CANCEL_PROOFING_TASK = 'on_cancel_proofing_task'

    # kwargs: request, article, proofing_task
    # raised when a proofing manager cancels a proofing task
    ON_EDIT_PROOFING_TASK = 'on_edit_proofing_task'

    # kwargs: request, proofing_task, decision
    # raised when a proofreader accepts or declines a task
    ON_PROOFREADER_TASK_DECISION = 'on_proofreader_task_decision'

    # kwargs: request, proofing_task, article
    # raised when a proofing task is completed
    ON_COMPLETE_PROOFING_TASK = 'on_complete_proofing_task'

    # kwargs: request, typeset_task, user_content_message, skip (boolean)
    # raised when a proofing manager requests changes from a typesetter.
    ON_PROOFING_TYPESET_CHANGES_REQUEST = 'on_proofing_typeset_changes_request'

    # kwargs: request, proofing_task, decision
    # raised when a typesetter accepts a proofing change request
    ON_PROOFING_TYPESET_DECISION = 'on_proofing_typeset_decision'

    # kwargs: request, correction_task, article
    # raised when a proofing manager cancels/deletes a correction task
    ON_CORRECTIONS_CANCELLED = 'on_corrections_cancelled'

    # kwargs: request, proofing_task, article
    # raised when a typesetter completes corrections
    ON_CORRECTIONS_COMPLETE = 'on_corrections_complete'

    # kwargs: request, article, user_message, model_object, model_name
    # raised when a Proofing Manager acks a proofing task
    ON_PROOFING_ACK = 'on_proofing_ack'

    # kwargs: request, article, user_message
    # raised when proofing is complete
    ON_PROOFING_COMPLETE = 'on_proofing_complete'

    #kwargs: request, article
    # raised when an article is marked as published
    ON_ARTICLE_PUBLISHED = 'on_article_published'

    # kwargs: request, article
    # raised when an Editor notifies an author that publication is set
    ON_AUTHOR_PUBLICATION = 'on_author_publication'

    # kwargs: request, override
    # raised when an Editor overrides review security
    ON_REVIEW_SECURITY_OVERRIDE = 'on_review_security_override'

    # kwargs: request, article
    # raised when a new preprint article is submitted
    ON_PREPRINT_SUBMISSION = 'on_preprint_submission'

    # kwargs: request, article
    # raised when a preprint is published in the repo
    ON_PREPRINT_PUBLICATION = 'on_preprint_publication'

    # kwargs: request, article, comment
    # raised when a new comment is submitted for a preprint
    ON_PREPRINT_COMMENT = 'on_preprint_comment'

    # kwargs: handshake_url, request, article, switch_stage (optional)
    # raised when a workflow element completes to hand over to the next one
    ON_WORKFLOW_ELEMENT_COMPLETE = 'on_workflow_element_complete'

    @staticmethod
    def raise_event(event_name, task_object=None, **kwargs):
        """
        Allows us to raise an event and call all subscribers
        :param event_name: the name of the event. This should usually be a constant from the above list.
        :param task_object: the associated article within a task that can be used for task teardown. This should always
        be an article for database safety.
        :param kwargs: the arguments to pass to the event
        :return: None
        """

        # destroy/complete tasks that have registered for this event
        if event_name != "destroy_tasks" and task_object is not None and isinstance(task_object,
                                                                                    submission_models.Article):
            kwargs['event'] = event_name
            kwargs['task_obj'] = task_object
            Events.raise_event('destroy_tasks', **kwargs)

        # fire hooked functions
        if event_name not in Events._hooks:
            return
        else:
            event_return = [func(**kwargs) for func in Events._hooks[event_name]]

            if event_return:
                return event_return[0]

    @staticmethod
    def register_for_event(event_name, *functions):
        """
        Register a function to fire on a specific event
        :param event_name: the name of the event
        :param functions: the functions to be called
        :return:
        """
        if event_name not in Events._hooks:
            Events._hooks[event_name] = []

        Events._hooks[event_name] += functions


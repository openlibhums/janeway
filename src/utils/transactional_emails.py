__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from utils import (
    notify_helpers,
    models as util_models,
    setting_handler,
    render_template,
)
from core import models as core_models
from review import logic as review_logic


def send_reviewer_withdrawl_notice(**kwargs):
    review_assignment = kwargs['review_assignment']
    request = kwargs['request']
    user_message_content = kwargs['user_message_content']

    if 'skip' not in kwargs:
        kwargs['skip'] = True

    skip = kwargs['skip']

    description = '{0}\'s review of "{1}" has been withdrawn by {2}'.format(review_assignment.reviewer.full_name(),
                                                                            review_assignment.article.title,
                                                                            request.user.full_name())
    if not skip:
        log_dict = {'level': 'Info', 'action_text': description, 'types': 'Review Withdrawl',
                    'target': review_assignment.article}
        notify_helpers.send_email_with_body_from_user(
            request,
            'subject_review_withdrawl',
            review_assignment.reviewer.email,
            user_message_content,
            log_dict=log_dict
        )
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_editor_unassigned_notice(request, message, assignment, skip=False):
    description = "{a.editor} unassigned from {a.article} by {r.user}".format(
            a=assignment,
            r=request,
    )

    if not skip:

        log_dict = {
                'level': 'Info', 'action_text': description,
                'types': 'Editor Unassigned',
                'target': assignment.article
        }

        notify_helpers.send_email_with_body_from_user(
                request,
                'subject_unassign_editor',
                assignment.editor.email,
                message,
                log_dict=log_dict,
        )
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_editor_assigned_acknowledgements_mandatory(**kwargs):
    """
    This function is called via the event handling framework and it notifies that an editor has been assigned.
    It is wired up in core/urls.py. It is different to the below function in that this is called when an editor is
    assigned, whereas the below is only called when the user opts to send a message to the editor.
    :param kwargs: a list of kwargs that includes editor_assignment, user_message_content, skip (boolean) and request
    :return: None
    """

    editor_assignment = kwargs['editor_assignment']
    article = editor_assignment.article
    request = kwargs['request']
    user_message_content = kwargs['user_message_content']

    if 'skip' not in kwargs:
        kwargs['skip'] = True

    skip = kwargs['skip']
    acknowledgement = kwargs['acknowledgement']

    description = '{0} was assigned as the editor for "{1}"'.format(editor_assignment.editor.full_name(),
                                                                    article.title)

    context = {
        'article': article,
        'request': request,
        'editor_assignment': editor_assignment
    }

    log_dict = {'level': 'Info',
                'action_text': description,
                'types': 'Editor Assignment',
                'target': article}

    # send to assigned editor
    if not skip:
        notify_helpers.send_email_with_body_from_user(
            request,
            'subject_editor_assignment',
            editor_assignment.editor.email,
            user_message_content,
            log_dict=log_dict
        )

    # send to editor
    if not acknowledgement:
        notify_helpers.send_slack(request, description, ['slack_editors'])
        notify_helpers.send_email_with_body_from_setting_template(request, 'editor_assignment',
                                                                  'subject_editor_assignment',
                                                                  request.user.email, context,
                                                                  log_dict=log_dict)


def send_editor_assigned_acknowledgements(**kwargs):
    """
    This function is called via the event handling framework and it notifies that an editor has been assigned.
    It is wired up in core/urls.py.
    :param kwargs: a list of kwargs that includes editor_assignment, user_message_content, skip (boolean) and request
    :return: None
    """
    kwargs['acknowledgement'] = True

    send_editor_assigned_acknowledgements_mandatory(**kwargs)


def send_reviewer_requested_acknowledgements(**kwargs):
    """
    This function is called via the event handling framework and it notifies that a reviewer has been requested.
    It is wired up in core/urls.py.
    :param kwargs: a list of kwargs that includes review_assignment, user_message_content, skip (boolean) and request
    :return: None
    """

    review_assignment = kwargs['review_assignment']
    article = review_assignment.article
    request = kwargs['request']
    user_message_content = kwargs['user_message_content']

    if 'skip' not in kwargs:
        kwargs['skip'] = True

    skip = kwargs['skip']

    description = 'A review request was added to "{0}" for user {1}'.format(
        article.title,
        review_assignment.reviewer.full_name(),
    )

    log_dict = {'level': 'Info',
                'action_text': description,
                'types': 'Review Request',
                'target': article}

    # send to requested reviewer
    if not skip:
        notify_helpers.send_email_with_body_from_user(
            request,
            'subject_review_assignment',
            review_assignment.reviewer.email,
            user_message_content,
            log_dict=log_dict,
        )

    # send slack
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_review_complete_acknowledgements(**kwargs):
    """
    This function is called via the event handling framework and it notifies that a reviewer has completed his or her
    review. It is wired up in core/urls.py.
    :param kwargs: a list of kwargs that includes review_assignment, and request
    :return: None
    """
    review_assignment = kwargs['review_assignment']
    article = review_assignment.article
    request = kwargs['request']
    request.user = review_assignment.reviewer

    description = '{0} completed the review of "{1}": {2}'.format(
        review_assignment.reviewer.full_name(),
        article.title,
        review_assignment.get_decision_display(),
    )

    util_models.LogEntry.add_entry(
        types='Review Complete',
        description=description,
        level='Info',
        actor=request.user,
        target=article,
        request=request,
    )

    review_in_review_url = request.journal.site_url(
        path=reverse(
            'review_in_review',
            kwargs={'article_id': article.pk},
        )
    )

    context = {
        'article': article,
        'request': request,
        'review_assignment': review_assignment,
    }

    # send slack
    notify_helpers.send_slack(request, description, ['slack_editors'])

    # send to reviewer
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'review_complete_reviewer_acknowledgement',
        'subject_review_complete_reviewer_acknowledgement',
        review_assignment.reviewer.email,
        context,
    )

    # send to editor
    context['review_in_review_url'] = review_in_review_url
    editors = get_assignment_editors(review_assignment)
    for editor in editors:
        notify_helpers.send_email_with_body_from_setting_template(
            request,
            'review_complete_acknowledgement',
            'subject_review_complete_acknowledgement',
            editor.email,
            context,
        )


def send_reviewer_accepted_or_decline_acknowledgements(**kwargs):
    """
    This function is called via the event handling framework and it notifies that a reviewer has either accepted or
    declined to review. It is wired up in core/urls.py.
    :param kwargs: a list of kwargs that includes review_assignment, accepted and request
    :return: None
    """
    review_assignment = kwargs['review_assignment']
    article = review_assignment.article
    request = kwargs['request']
    accepted = kwargs['accepted']

    description = '{0} {1} to review {2}'.format(
        review_assignment.reviewer.full_name(),
        ('accepted' if accepted else 'declined'),
        article.title,
    )

    util_models.LogEntry.add_entry(
        types='Review request {0}'.format(('accepted' if accepted else 'declined')),
        description=description,
        level='Info',
        actor=request.user,
        target=article,
        request=request,
    )

    review_url = review_logic.get_review_url(
        request,
        review_assignment,
    )

    review_in_review_url = request.journal.site_url(
        path=reverse(
            'review_in_review',
            kwargs={'article_id': article.pk},
        )
    )

    context = {
        'article': article,
        'request': request,
        'review_assignment': review_assignment,
    }

    reviewer_context = context
    reviewer_context['review_url'] = review_url
    editor_context = context
    editor_context['review_in_review_url'] = review_in_review_url

    # send to slack
    notify_helpers.send_slack(request, description, ['slack_editors'])

    # send to reviewer
    if accepted:
        context["reviewer_decision"] = _("accepted")
        notify_helpers.send_email_with_body_from_setting_template(
            request,
            'review_accept_acknowledgement',
            'subject_review_accept_acknowledgement',
            review_assignment.reviewer.email,
            reviewer_context,
        )

    else:
        context["reviewer_decision"] = _("declined")
        notify_helpers.send_email_with_body_from_setting_template(
            request,
            'review_decline_acknowledgement',
            'subject_review_decline_acknowledgement',
            review_assignment.reviewer.email,
            reviewer_context,
        )

    # send to editor
    editors = get_assignment_editors(review_assignment)
    for editor in editors:
        notify_helpers.send_email_with_body_from_setting_template(
            request,
            'reviewer_acknowledgement',
            'subject_reviewer_acknowledgement',
            editor.email,
            editor_context,
        )


def send_submission_acknowledgement(**kwargs):
    """
    This function is called via the event handling framework and it
    notifies site operators of a submission. It is
    wired up in core/urls.py.
    :param kwargs: a list of kwargs that includes article and request
    :return: None
    """

    article = kwargs['article']
    request = kwargs['request']

    util_models.LogEntry.add_entry(
        types='Submission Complete',
        description='A new article {0} was submitted'.format(article.title),
        level='Info',
        actor=request.user,
        target=article,
        request=request,
    )

    log_dict = {
        'level': 'Info',
        'action_text': 'A new article {0} was submitted'.format(article.title),
        'types': 'New Submission Acknowledgement',
        'target': article,
    }

    # generate URL
    review_unassigned_article_url = request.journal.site_url(
        path=reverse(
            'review_unassigned_article',
            kwargs={'article_id': article.pk},
        )
    )
    notify_helpers.send_slack(
        request,
        'New submission: {0} {1}'.format(
            article.title,
            review_unassigned_article_url,
        ),
        ['slack_editors'])

    # send to author
    context = {
        'article': article,
        'request': request,
        'review_unassigned_article_url': review_unassigned_article_url,
    }
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'submission_acknowledgement',
        'subject_submission_acknowledgement',
        article.correspondence_author.email,
        context,
        log_dict=log_dict,
    )

    # send to all authors
    editors_to_email = setting_handler.get_setting(
        'general', 'editors_for_notification', request.journal).processed_value

    if editors_to_email:
        editor_pks = [int(pk) for pk in editors_to_email]
        editor_emails = {
            role.user.email for role in core_models.AccountRole.objects.filter(
                role__slug='editor',
                user__id__in=editor_pks,
            )
        }
    else:
        editor_emails = set(request.journal.editor_emails)

    assigned_to_section = (
        article.section.editors.all() | article.section.section_editors.all())

    editor_emails |= {editor.email for editor in assigned_to_section}

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'editor_new_submission',
        'subject_editor_new_submission',
        editor_emails,
        context,
        log_dict=log_dict,
    )


def send_article_decision(**kwargs):
    article = kwargs['article']
    request = kwargs['request']
    decision = kwargs['decision']
    user_message_content = kwargs['user_message_content']

    if 'skip' not in kwargs:
        kwargs['skip'] = True

    skip = kwargs['skip']

    description = '{0}\'s article "{1}" has been {2}ed by {3}'.format(article.correspondence_author.full_name(),
                                                                      article.title,
                                                                      decision,
                                                                      request.user.full_name())

    log_dict = {'level': 'Info',
                'action_text': description,
                'types': 'Article Decision',
                'target': article}

    if decision == 'accept':
        subject = 'subject_review_decision_accept'
    elif decision == 'decline':
        subject = 'subject_review_decision_decline'
    elif decision == 'undecline':
        subject = 'subject_review_decision_undecline'


    if not skip:
        notify_helpers.send_email_with_body_from_user(
            request,
            subject,
            article.correspondence_author.email,
            user_message_content,
            log_dict=log_dict
        )
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_revisions_request(**kwargs):
    request = kwargs['request']
    revision = kwargs['revision']
    user_message_content = kwargs['user_message_content']

    if 'skip' not in kwargs:
        kwargs['skip'] = True

    skip = kwargs['skip']

    description = '{0} has requested revisions for {1} due on {2}'.format(
        request.user.full_name(),
        revision.article.title,
        revision.date_due,
    )

    log_dict = {'level': 'Info',
                'action_text': description,
                'types': 'Revision Request',
                'target': revision.article,
                }

    if not skip:
        notify_helpers.send_email_with_body_from_user(
            request,
            'subject_request_revisions',
            revision.article.correspondence_author.email,
            user_message_content,
            log_dict=log_dict,
        )
        notify_helpers.send_slack(
            request,
            description,
            ['slack_editors'],
        )


def send_revisions_complete(**kwargs):
    request = kwargs['request']
    revision = kwargs['revision']

    action_text = ''
    for action in revision.actions.all():
        action_text = "{0}<br><br>{1} - {2}".format(action_text, action.logged, action.text)

    description = ('<p>{0} has completed revisions for {1}</p> Actions:<br>{2}'
        ''.format(request.user.full_name(), revision.article.title, action_text)
    )
    notify_helpers.send_email_with_body_from_user(
        request,
        'subject_revisions_complete_receipt',
        {editor.email for editor in get_assignment_editors(revision)},
        description,
    )
    notify_helpers.send_slack(request, description, ['slack_editors'])

    util_models.LogEntry.add_entry(
        types='Revisions Complete', description=action_text, level='Info',
        request=request, target=revision.article,
    )


def send_revisions_author_receipt(**kwargs):
    request = kwargs['request']
    revision = kwargs['revision']

    description = '{0} has completed revisions for {1}'.format(
        request.user.full_name(),
        revision.article.title,
    )
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Revisions Complete',
        'target': revision.article,
    }
    context = {
        'revision': revision,
    }
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'revisions_complete_receipt',
        'subject_revisions_complete_receipt',
        revision.article.correspondence_author.email,
        context,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(
        request,
        description,
        ['slack_editors'],
    )


def send_copyedit_assignment(**kwargs):
    request = kwargs['request']
    copyedit_assignment = kwargs['copyedit_assignment']
    user_message_content = kwargs['user_message_content']
    skip = kwargs.get('skip', False)

    description = '{0} has requested copyediting for {1} due on {2}'.format(
        request.user.full_name(),
        copyedit_assignment.article.title,
        copyedit_assignment.due,
    )

    if not skip:
        log_dict = {
            'level': 'Info', 'action_text': description,
            'types': 'Copyedit Assignment',
            'target': copyedit_assignment.article,
        }
        response = notify_helpers.send_email_with_body_from_user(
            request, 'subject_copyeditor_assignment_notification',
            copyedit_assignment.copyeditor.email,
            user_message_content, log_dict,
        )
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_copyedit_updated(**kwargs):
    request = kwargs['request']
    copyedit_assignment = kwargs['copyedit_assignment']
    skip = kwargs.get('skip', False)

    if not skip:
        # send to slack
        notify_helpers.send_slack(request,
                                  'Copyedit assignment {0} updated'.format(copyedit_assignment.pk),
                                  ['slack_editors'])

        log_dict = {'level': 'Info',
                    'action_text': 'Copyedit assignment #{number} update.'.format(number=copyedit_assignment.pk),
                    'types': 'Revision Request',
                    'target': copyedit_assignment.article}

        # send to author
        notify_helpers.send_email_with_body_from_setting_template(request,
                                                                  'copyedit_updated',
                                                                  'subject_copyedit_updated',
                                                                  copyedit_assignment.copyeditor.email,
                                                                  context={'request': request,
                                                                           'copyedit_assignment': copyedit_assignment},
                                                                  log_dict=log_dict)


def send_copyedit_deleted(**kwargs):
    request = kwargs['request']
    copyedit_assignment = kwargs['copyedit_assignment']
    skip = kwargs.get('skip', False)

    description = 'Copyedit task {0} for article {1} deleted.'.format(copyedit_assignment.pk,
                                                                      copyedit_assignment.article.title)

    if not skip:
        # send to slack
        notify_helpers.send_slack(request,
                                  'Copyedit assignment {0} updated'.format(copyedit_assignment.pk),
                                  ['slack_editors'])

        log_dict = {'level': 'Info', 'action_text': description, 'types': 'Copyedit Assignment Deleted',
                    'target': copyedit_assignment.article}
        # send to copyeditor
        notify_helpers.send_email_with_body_from_setting_template(request,
                                                                  'copyedit_deleted',
                                                                  'subject_copyedit_deleted',
                                                                  copyedit_assignment.copyeditor.email,
                                                                  context={'request': request,
                                                                           'copyedit_assignment': copyedit_assignment},
                                                                  log_dict=log_dict)


def send_copyedit_decision(**kwargs):
    request = kwargs['request']
    decision = kwargs["decision"]
    copyedit_assignment = kwargs['copyedit_assignment']

    description = '{0} has {1}ed copyediting task for {2} due on {3}.'.format(
        copyedit_assignment.copyeditor.full_name(),
        decision,
        copyedit_assignment.article.title,
        copyedit_assignment.due)

    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Copyediting Decision',
                'target': copyedit_assignment.article}

    notify_helpers.send_email_with_body_from_user(request, 'subject_copyediting_decision',
                                                  copyedit_assignment.editor.email,
                                                  description, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_copyedit_author_review(**kwargs):
    request = kwargs['request']
    copyedit_assignment = kwargs['copyedit_assignment']
    user_message_content = kwargs['user_message_content']
    skip = kwargs.get('skip', False)

    description = '{0} has requested copyedit review for {1} from {2}'.format(
        request.user.full_name(),
        copyedit_assignment.article.title,
        copyedit_assignment.article.correspondence_author.full_name())

    if not skip:
        log_dict = {'level': 'Info', 'action_text': description, 'types': 'Copyedit Author Review',
                    'target': copyedit_assignment.article}

        notify_helpers.send_email_with_body_from_user(request, 'subject_copyeditor_notify_author',
                                                      copyedit_assignment.article.correspondence_author.email,
                                                      user_message_content, log_dict=log_dict)
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_copyedit_complete(**kwargs):
    request = kwargs['request']
    copyedit_assignment = kwargs['copyedit_assignment']
    article = kwargs['article']

    description = 'Copyediting requested by {0} from {1} for article {2} ' \
        'has been completed'.format(
            request.user.full_name(),
            copyedit_assignment.copyeditor.full_name(),
            article.title
    )

    log_dict = {
        'level': 'Info', 'action_text': description,
        'types': 'Copyedit Complete',
        'target': article,
    }
    article_copyediting_url = request.journal.site_url(reverse(
        'article_copyediting', args=[article.pk],
    ))

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'copyeditor_notify_editor',
        'subject_copyeditor_notify_editor',
        copyedit_assignment.editor.email,
        context={
            'assignment': copyedit_assignment,
            'article_copyediting_url': article_copyediting_url,
        },
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_author_copyedit_deleted(**kwargs):
    request = kwargs.get('request')
    author_review = kwargs.get('author_review')
    subject = kwargs.get('subject')
    user_message_content = kwargs.get('user_message_content')
    skip = kwargs.get('skip', False)

    description = '{0} has deleted a copyedit review for {1} from {2}'.format(
        request.user.full_name(),
        author_review.assignment.article.title,
        author_review.assignment.article.correspondence_author.full_name(),
    )
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Author Copyedit Review Deleted',
        'target': author_review.assignment.article,
    }

    if not skip:
        notify_helpers.send_email_with_body_from_user(
            request,
            subject,
            author_review.assignment.article.correspondence_author.email,
            user_message_content,
            log_dict=log_dict,
        )
    else:
        util_models.LogEntry.add_entry(
            'Author Copyedit Review Deleted',
            description,
            'Info',
            request.user,
            request,
            author_review.assignment.article,
        )


def send_copyedit_ack(**kwargs):
    request = kwargs['request']
    copyedit_assignment = kwargs['copyedit_assignment']
    user_message_content = kwargs['user_message_content']
    skip = kwargs.get('skip', False)

    description = '{0} has acknowledged copyediting for {1}'.format(request.user.full_name(),
                                                                    copyedit_assignment.article.title, )

    if not skip:
        log_dict = {'level': 'Info', 'action_text': description, 'types': 'Copyedit Acknowledgement',
                    'target': copyedit_assignment.article}

        notify_helpers.send_email_with_body_from_user(request, 'subject_copyeditor_ack',
                                                      copyedit_assignment.copyeditor.email,
                                                      user_message_content, log_dict=log_dict)
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_copyedit_reopen(**kwargs):
    request = kwargs['request']
    copyedit_assignment = kwargs['copyedit_assignment']
    user_message_content = kwargs['user_message_content']
    skip = kwargs.get('skip', False)

    description = '{0} has reopened copyediting for {1} from {2}'.format(request.user.full_name(),
                                                                         copyedit_assignment.article.title,
                                                                         copyedit_assignment.copyeditor.full_name())

    if not skip:
        log_dict = {'level': 'Info', 'action_text': description, 'types': 'Copyedit Complete',
                    'target': copyedit_assignment.article}

        notify_helpers.send_email_with_body_from_user(request, 'subject_copyeditor_reopen_task',
                                                      copyedit_assignment.copyeditor.email,
                                                      user_message_content, log_dict=log_dict)
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_typeset_assignment(**kwargs):
    request = kwargs['request']
    typeset_task = kwargs['typeset_task']
    user_message_content = kwargs['user_message_content']
    skip = kwargs.get('skip', False)

    description = '{0} has been assigned as a typesetter for {1}'.format(typeset_task.typesetter.full_name(),
                                                                         typeset_task.assignment.article.title)

    if not skip:
        log_dict = {'level': 'Info', 'action_text': description, 'types': 'Typesetting Assignment',
                    'target': typeset_task.assignment.article}

        notify_helpers.send_email_with_body_from_user(request, 'subject_typesetter_notification',
                                                      typeset_task.typesetter.email,
                                                      user_message_content, log_dict=log_dict)
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_typeset_decision(**kwargs):
    request = kwargs['request']
    typeset_task = kwargs['typeset_task']
    decision = kwargs['decision']

    description = '{0} has {1}ed the typesetting task for {2}'.format(typeset_task.typesetter.full_name(),
                                                                      decision,
                                                                      typeset_task.assignment.article.title)

    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Typesetter Decision',
                'target': typeset_task.assignment.article}

    notify_helpers.send_email_with_body_from_user(request, 'Article Typesetting Decision',
                                                  typeset_task.assignment.production_manager.email,
                                                  description, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_typeset_task_deleted(**kwargs):
    request = kwargs['request']
    typeset_task = kwargs['typeset']

    description = '{0} has deleted a typesetter task assigned to {1} for article {2}'.format(
        request.user.full_name(),
        typeset_task.typesetter.full_name(),
        typeset_task.assignment.article.title,
    )

    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Typesetter Assignment Deleted',
                'target': typeset_task.assignment.article}

    # send to author
    notify_helpers.send_email_with_body_from_setting_template(request,
                                                              'typeset_deleted',
                                                              'subject_typeset_deleted',
                                                              typeset_task.typesetter.email,
                                                              context={'request': request,
                                                                       'typeset_task': typeset_task}, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_typeset_complete(**kwargs):
    request = kwargs['request']
    typeset_task = kwargs['typeset_task']

    description = '{0} has completed typesetting for article {1}. \n\nThe following note was supplied:\n\n{2}'.format(
        typeset_task.typesetter.full_name(),
        typeset_task.assignment.article.title,
        typeset_task.note_from_typesetter,
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Typesetting Assignment Complete',
        'target': typeset_task.assignment.article,
    }

    production_article_url = request.journal.site_url(
        path=reverse(
            'production_article',
            kwargs={'article_id': typeset_task.assignment.article.pk},
        )
    )

    context = {
        'production_article_url': production_article_url,
        'typeset_task': typeset_task,
        'production_assignment': typeset_task.assignment,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'typesetter_complete_notification',
        'subject_typesetter_complete_notification',
        typeset_task.assignment.production_manager.email,
        context,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_production_complete(**kwargs):
    request = kwargs['request']
    article = kwargs['article']
    user_content_message = kwargs['user_content_message']
    assignment = kwargs['assignment']

    description = 'Production has been completed for article {0}.'.format(article.title)

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Production Complete',
        'target': article,
    }

    for task in assignment.typesettask_set.all():
        notify_helpers.send_email_with_body_from_user(
            request,
            'Article Production Complete',
            task.typesetter.email,
            user_content_message,
        )

    context = {
        'article': article,
        'assignment': assignment,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'production_complete',
        'subject_production_complete',
        article.editor_emails(),
        context,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ['slack_editors'])


def fire_proofing_manager_assignment(**kwargs):
    request = kwargs['request']
    proofing_assignment = kwargs['proofing_assignment']
    article = proofing_assignment.article

    description = '{0} has been assigned as proofing manager for {1}'.format(
        proofing_assignment.proofing_manager.full_name(),
        article.title,
    )
    log_dict = {
        'level': 'Info', 'action_text': description,
        'types': 'Proofing Manager Assigned',
        'target': article,
    }

    proofing_url = request.journal.site_url(reverse(
        'proofing_article', args=[article.pk]
    ))

    context = {
        'request': request,
        'proofing_assignment': proofing_assignment,
        'article': article,
        'proofing_article_url': proofing_url,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'notify_proofing_manager',
        'subject_notify_proofing_manager',
        proofing_assignment.proofing_manager.email,
        context,
        log_dict=log_dict,
    )

    notify_helpers.send_slack(request, description, ['slack_editors'])


def cancel_proofing_task(**kwargs):
    request = kwargs['request']
    article = kwargs['article']
    proofing_task = kwargs['proofing_task']
    user_content_message = kwargs.get('user_content_message', '')

    description = 'Proofing request for article {0} from {1} has been cancelled by {2}'.format(
        article.title,
        proofing_task.proofreader.full_name(),
        request.user.full_name()
    )
    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Proofing Task Cancelled',
                'target': article}
    context = {'request': request, 'proofing_task': proofing_task, 'user_content_message': user_content_message}
    notify_helpers.send_email_with_body_from_setting_template(request,
                                                              'notify_proofreader_cancelled',
                                                              'subject_notify_proofreader_cancelled',
                                                              proofing_task.proofreader.email,
                                                              context, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])


def edit_proofing_task(**kwargs):
    request = kwargs['request']
    article = kwargs['article']
    proofing_task = kwargs['proofing_task']

    description = 'Proofing request for article {0} from {1} has been edited by {2}'.format(
        article.title,
        proofing_task.proofreader.full_name(),
        request.user.full_name()
    )
    context = {'request': request, 'proofing_task': proofing_task}
    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Proofing Task Edited',
                'target': article}
    notify_helpers.send_email_with_body_from_setting_template(request,
                                                              'notify_proofreader_edited',
                                                              'subject_notify_proofreader_edited',
                                                              proofing_task.proofreader.email,
                                                              context, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])


def notify_proofreader(**kwargs):
    request = kwargs['request']
    article = kwargs['article']
    proofing_task = kwargs['proofing_task']
    user_content_message = kwargs['user_content_message']

    description = 'Proofing request for article {0} from {1} has been requested by {2}'.format(
        article.title,
        proofing_task.proofreader.full_name(),
        request.user.full_name()
    )
    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Proofreading Requested',
                'target': article}
    notify_helpers.send_email_with_body_from_user(request, 'subject_notify_proofreader_assignment',
                                                  proofing_task.proofreader.email,
                                                  user_content_message, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_proofreader_decision(**kwargs):
    request = kwargs['request']
    proofing_task = kwargs['proofing_task']
    decision = kwargs['decision']

    description = '{0} has made a decision for proofing task on {1}: {2}'.format(
        proofing_task.proofreader.full_name(),
        proofing_task.round.assignment.article.title,
        decision
    )
    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Proofreading Update',
                'target': proofing_task.round.assignment.article}
    notify_helpers.send_email_with_body_from_user(request, 'Article Proofreading Update',
                                                  proofing_task.round.assignment.proofing_manager.email,
                                                  description, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_proofreader_complete_notification(**kwargs):
    request = kwargs['request']
    proofing_task = kwargs['proofing_task']
    article = kwargs['article']

    description = '{0} has completed a proofing task for {1}'.format(
        proofing_task.proofreader.full_name(),
        article.title,
    )
    proofing_url = request.journal.site_url(reverse(
        'proofing_article', args=[article.pk]
    ))
    context = {
        'proofing_task': proofing_task,
        'proofing_article_url': proofing_url,

    }
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'notify_proofreader_complete',
        'subject_notify_proofreader_complete',
        proofing_task.round.assignment.proofing_manager.email,
        context,
    )
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_proofing_typeset_request(**kwargs):
    request = kwargs['request']
    typeset_task = kwargs['typeset_task']
    article = kwargs['article']
    user_content_message = kwargs['user_content_message']
    skip = kwargs['skip']

    description = '{0} has requested typesetting updates from {1} for {2}'.format(
        request.user.full_name(),
        typeset_task.typesetter.full_name(),
        article.title,
    )
    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Typesetting Updates Requested',
                'target': article}
    if not skip:
        notify_helpers.send_slack(request, description, ['slack_editors'])
        notify_helpers.send_email_with_body_from_user(
            request, 'subject_notify_typesetter_proofing_changes',
            typeset_task.typesetter.email,
            user_content_message, log_dict=log_dict)


def send_proofing_typeset_decision(**kwargs):
    request = kwargs['request']
    typeset_task = kwargs['typeset_task']
    decision = kwargs['decision']

    description = '{0} has made a decision for proofing task on {1}: {2}'.format(
        typeset_task.typesetter.full_name(),
        typeset_task.proofing_task.round.assignment.article.title,
        decision
    )
    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Proofing Typesetting',
                'target': typeset_task.proofing_task.round.assignment.article}
    notify_helpers.send_email_with_body_from_user(request, 'Proofing Typesetting Changes',
                                                  typeset_task.proofing_task.round.assignment.proofing_manager.email,
                                                  description, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_corrections_complete(**kwargs):
    request = kwargs['request']
    typeset_task = kwargs['typeset_task']
    article = kwargs['article']

    description = '{0} has completed corrections task for article {1} (proofing task {2})'.format(
        request.user.full_name(),
        article.title,
        typeset_task.pk,
    )
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Proofing Typesetting Complete',
        'target': typeset_task.proofing_task.round.assignment.article,
    }
    proofing_article_url = request.journal.site_url(
        path=reverse(
            'production_article',
            kwargs={'article_id': typeset_task.proofing_task.assignment.article.pk},
        )
    )
    context = {
        'typeset_task': typeset_task,
        'proofing_article_url': proofing_article_url,
        'production_assignment': typeset_task.proofing_task.assignment,
    }
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'typesetter_corrections_complete',
        'subject_typesetter_corrections_complete',
        article.proofingassignment.proofing_manager.email,
        context,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_proofing_ack(**kwargs):
    request = kwargs['request']
    user_message = kwargs['user_message']
    article = kwargs['article']
    model_object = kwargs['model_object']
    model_name = kwargs['model_name']
    skip = kwargs['skip']

    description = "{0} has acknowledged a task , {1}, by {2} for article {3}".format(request.user,
                                                                                     model_name,
                                                                                     model_object.actor().full_name(),
                                                                                     article.title)

    if not skip:
        notify_helpers.send_email_with_body_from_user(request, 'Proofing Acknowledgement',
                                                      model_object.actor().email,
                                                      user_message)
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_proofing_complete(**kwargs):
    request = kwargs['request']
    user_message = kwargs['user_message']
    article = kwargs['article']
    skip = kwargs['skip']

    description = "Proofing is now complete for {0}".format(article.title)
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Proofing Complete',
        'target': article,
    }
    if not skip:
        notify_helpers.send_email_with_body_from_user(
            request,
            'subject_notify_editor_proofing_complete',
            article.editor_emails(),
            user_message,
            log_dict=log_dict,
        )
        notify_helpers.send_slack(request, description, ['slack_editors'])


def send_author_publication_notification(**kwargs):
    request = kwargs['request']
    article = kwargs['article']
    user_message = kwargs['user_message']
    section_editors = kwargs['section_editors']
    peer_reviewers = kwargs['peer_reviewers']

    description = "Article, {0}, set for publication on {1}, by {2}".format(article.title,
                                                                            article.date_published,
                                                                            request.user.full_name())

    log_dict = {'level': 'Info', 'action_text': description, 'types': 'Article Published',
                'target': article}

    notify_helpers.send_email_with_body_from_user(request,
                                                  'subject_author_publication',
                                                  article.correspondence_author.email,
                                                  user_message, log_dict=log_dict)
    notify_helpers.send_slack(request, description, ['slack_editors'])

    # Check for SEs and PRs and notify them as well
    if section_editors:
        for editor in article.section_editors():
            notify_helpers.send_email_with_body_from_setting_template(
                request,
                'section_editor_pub_notification',
                'subject_section_editor_pub_notification',
                editor.email,
                {'article': article, 'editor': editor},
            )

    if peer_reviewers:
        reviewers = {review_assignment.reviewer for review_assignment in article.completed_reviews_with_decision}
        for reviewer in reviewers:
            notify_helpers.send_email_with_body_from_setting_template(
                request,
                'peer_reviewer_pub_notification',
                'subject_peer_reviewer_pub_notification',
                reviewer.email,
                {'article': article, 'reviewer': reviewer},
            )


def review_sec_override_notification(**kwargs):
    request = kwargs['request']
    override = kwargs['override']

    description = "{0} overrode their access to {1}".format(override.editor.full_name(), override.article.title)
    log_dict = {'level': 'Warning', 'action_text': description, 'types': 'Security Override',
                'target': override.article}
    notify_helpers.send_slack(request, description, ['slack_editors'])
    notify_helpers.send_email_with_body_from_user(request, 'Review Security Override',
                                                  request.journal.editor_emails,
                                                  description, log_dict=log_dict)


def send_draft_decison(**kwargs):
    request = kwargs['request']
    draft = kwargs['draft']
    article = kwargs['article']

    description = "Section Editor {0} has drafted a decision for Article {1}".format(
        draft.section_editor.full_name(), article.title)
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Draft Decision',
        'target': article,
    }
    review_edit_draft_decision_url = request.journal.site_url(
        path=reverse(
            'review_edit_draft_decision', args=[article.pk, draft.pk]
        )
    )
    context = {
        'draft': draft,
        'article': article,
        'review_edit_draft_decision_url': review_edit_draft_decision_url,
    }
    notify_helpers.send_slack(request, description, ['slack_editors'])
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'draft_editor_message',
        'subject_draft_editor_message',
        draft.editor.email if draft.editor else request.journal.editor_emails,
        context,
        log_dict=log_dict,
    )


def send_author_copyedit_complete(**kwargs):
    request = kwargs['request']
    copyedit = kwargs['copyedit']
    author_review = kwargs['author_review']

    editor_review_url = request.journal.site_url(
        path=reverse(
            'editor_review',
            kwargs={
                'article_id': copyedit.article.pk,
                'copyedit_id': copyedit.pk,
            }
        )
    )
    description = "Author {0} has completed their copyediting task for article {1}".format(
        author_review.author.full_name(),
        copyedit.article.title,
    )
    context = {
        'copyedit': copyedit,
        'author_review': author_review,
        'editor_review_url': editor_review_url,
    }
    notify_helpers.send_slack(request, description, ['slack_editors'])
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'author_copyedit_complete',
        'subject_author_copyedit_complete',
        copyedit.editor.email,
        context,
    )


def preprint_submission(**kwargs):
    """
    Called by events.Event.ON_PRePINT_SUBMISSIONS, logs and emails the author
    and preprint editor.
    :param kwargs: Dictionary containing article and request objects
    :return: None
    """
    request = kwargs.get('request')
    preprint = kwargs.get('preprint')

    description = '{author} has submitted a new {obj} titled {title}.'.format(
        author=request.user.full_name(),
        obj=request.repository.object_name,
        title=preprint.title,
    )
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Submission',
        'target': preprint,
    }

    # Send an email to the user
    context = {'preprint': preprint}
    template = request.repository.submission
    email_text = render_template.get_message_content(
        request,
        context,
        template,
        template_is_setting=True,
    )
    notify_helpers.send_email_with_body_from_user(
        request,
        '{} Submission'.format(request.repository.object_name),
        request.user.email,
        email_text,
        log_dict=log_dict,
    )

    # Send an email to the preprint editor
    url = request.repository.site_url() + reverse(
        'repository_manager_article',
        kwargs={'preprint_id': preprint.pk},
    )
    editor_email_text = 'A new {object} has been submitted to {press}: <a href="{url}">{title}</a>.'.format(
        object=request.repository.object_name,
        press=request.repository.name,
        url=url,
        title=preprint.title
    )
    repo = request.repository
    recipients = repo.submission_notification_recipients if repo.submission_notification_recipients.count() > 0 else repo.managers
    for r in recipients.all():
        notify_helpers.send_email_with_body_from_user(
            request,
            '{} Submission'.format(request.repository.object_name),
            r.email,
            editor_email_text,
            log_dict=log_dict,
        )


def preprint_notification(**kwargs):
    """
    Called by events.Event.ON_PREPRINT_NOTIFICATION handles logging and emails.
    :param kwargs: Dict with preprint, content and request objects
    :return: None
    """
    request = kwargs.get('request')
    preprint = kwargs.get('preprint')
    content = kwargs.get('email_content')
    skip = kwargs.get('skip')

    if preprint.date_declined:
        types = 'Rejected'
        description = '<p>{editor} has rejected \'{title}\'. Moderator reason:</p><p>{reason}</p>'.format(
            editor=request.user.full_name(),
            title=preprint.title,
            reason=preprint.preprint_decline_note,
        )
    else:
        types = 'Accepted'
        description = '{editor} has published \'{title}\'.'.format(
            editor=request.user.full_name(),
            title=preprint.title,
        )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': types,
        'target': preprint,
    }

    util_models.LogEntry.add_entry(
        types,
        description,
        'Info',
        request.user,
        request,
        preprint,
    )

    if not skip:
        notify_helpers.send_email_with_body_from_user(
            request,
            '{} Submission Decision'.format(preprint.title),
            preprint.owner.email,
            content,
            log_dict=log_dict,
        )

        # Stops this notification being sent multiple times.c
        preprint.preprint_decision_notification = True
        preprint.save()


def preprint_comment(**kwargs):
    request = kwargs.get('request')
    preprint = kwargs.get('preprint')

    path = reverse(
        'repository_comments',
        kwargs={'preprint_id': preprint.pk},
    )
    url = request.repository.site_url(path)

    email_text = 'A comment has been made on your article {title}, you can moderate comments ' \
                 '<a href="{url}">on the journal site</a>.'.format(
        title=preprint.title,
        url=url,
    )

    description = '{author} commented on {title}'.format(
        author=request.user.full_name(),
        title=preprint.title,
    )
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Preprint Comment',
        'target': preprint,
    }

    notify_helpers.send_email_with_body_from_user(
        request,
        'Preprint Comment',
        preprint.owner.email,
        email_text,
        log_dict=log_dict,
    )


def preprint_version_update(**kwargs):
    request = kwargs.get('request')
    pending_update = kwargs.get('pending_update')
    action = kwargs.get('action')
    reason = kwargs.get('reason')

    description = '{object} Pending Version {pk}: Decision: {decision}'.format(
        object=request.repository.object_name,
        pk=pending_update.pk,
        decision=action,
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Preprint Publication',
        'target': pending_update.preprint,
    }

    context = {
        'pending_update': pending_update,
        'reason': reason,
    }

    if action == 'accept':
        template = request.repository.accept_version
        email_text = render_template.get_message_content(
            request,
            context,
            template,
            template_is_setting=True,
        )
    else:
        template = request.repository.decline_version
        email_text = render_template.get_message_content(
            request,
            context,
            template,
            template_is_setting=True,
        )
    notify_helpers.send_email_with_body_from_user(
        request,
        '{} Version Update'.format(pending_update.preprint.title),
        pending_update.preprint.owner.email,
        email_text,
        log_dict=log_dict,
    )


def send_cancel_corrections(**kwargs):
    request = kwargs.get('request')
    article = kwargs.get('article')
    correction = kwargs.get('correction')

    description = '{user} has cancelled correction task {task}'.format(
        user=request.user,
        task=correction,
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Correction Cancelled',
        'target': article,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'notify_correction_cancelled',
        'subject_notify_correction_cancelled',
        correction.typesetter.email,
        context=kwargs,
        log_dict=log_dict,
    )


def get_assignment_editors(assignment):
    """ Get editors relevant to a review or revision assignment

    This is a helper function to retrieve the editors that should be
    notified of changes in a review/ revision assignment.
    It exists to handle edge-cases where anassignment might not have an editor
    assigned (e.g.: migrated submissions from another system)
    :param assignment: an instance of ReviewAssignment or RevisionRequest
    :return: A list of Account objects
    """
    article = assignment.article
    if assignment.editor:
        editors = [assignment.editor]
    elif article.editorassignment_set.exists():
        # Try article assignment
        editors = [ass.editor for ass in article.editorassignment_set.all()]
    else:
        # Fallback to all editors
        editors = [e for e in assignment.article.journal.editors()]
    return editors


def send_draft_decision_declined(**kwargs):
    request = kwargs.get('request')
    article = kwargs.get('article')
    draft_decision = kwargs.get('draft_decision')

    description = '{user} has declined a draft decision {draft} written by {section_editor}'.format(
        user=request.user,
        draft=draft_decision.pk,
        section_editor=draft_decision.section_editor.full_name,
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Draft Decision Declined',
        'target': article,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'notify_se_draft_declined',
        'subject_notify_se_draft_declined',
        draft_decision.section_editor.email,
        context=kwargs,
        log_dict=log_dict,
    )


def access_request_notification(**kwargs):
    request = kwargs.get('request')
    access_request = kwargs.get('access_request')
    description = '{} has requested the {} role for {}'.format(
        request.user,
        access_request.role.name,
        request.site_type.name,
    )

    if request.journal:
        contact = request.journal.get_setting('general', 'submission_access_request_contact')
    else:
        contact = request.repository.submission_access_contact

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Access Request',
        'target': request.site_type,
    }
    if contact:
        notify_helpers.send_email_with_body_from_setting_template(
            request,
            'submission_access_request_notification',
            'subject_submission_access_request_notification',
            contact,
            context={'description': description},
            log_dict=log_dict,
        )


def access_request_complete(**kwargs):
    request = kwargs.get('request')
    access_request = kwargs.get('access_request')
    decision = kwargs.get('decision')
    description = "Access request from {} evaluated by {}: {}".format(
        access_request.user.full_name,
        request.user,
        decision,
    )
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Access Request',
        'target': request.site_type,
    }
    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'submission_access_request_complete',
        'subject_submission_access_request_complete',
        access_request.user.email,
        context={
            'access_request': access_request,
            'decision': decision,
        },
        log_dict=log_dict,
    )


def preprint_review_notification(**kwargs):
    request = kwargs.get('request')
    preprint = kwargs.get('preprint')
    review = kwargs.get('review')
    message = kwargs.get('message')
    skip = kwargs.get('skip', None)

    if not skip:
        description = 'Review of {} requested from {} by {}.'.format(
            preprint.title,
            review.reviewer.full_name(),
            review.manager.full_name(),
        )
        log_dict = {
            'level': 'Info',
            'action_text': description,
            'types': 'Review',
            'target': preprint,
        }
        notify_helpers.send_email_with_body_from_user(
            request,
            '{} Review Invitation'.format(request.repository.object_name),
            review.reviewer.email,
            message,
            log_dict=log_dict,
        )


def preprint_review_status_change(**kwargs):
    request = kwargs.get('request')
    review = kwargs.get('review')
    status_change = kwargs.get('status_change')
    status_text = None

    description = "Status of review {} by {} is now: {}".format(
        review.pk,
        review.reviewer.full_name(),
        status_change,
    )
    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Review',
        'target': review.preprint,
    }

    if status_change in ['accept', 'decline', 'complete']:
        to = review.manager.email
        if status_change == 'accept':
            status_text = 'The reviewer has agreed to add a comment.'
        elif status_change == 'decline':
            status_text = 'The reviewer has declined to add a comment.'
        elif status_change == 'complete':
            status_text = 'The reviewer has submitted their comment.'
        template = request.repository.manager_review_status_change
    else:  # withdraw
        to = review.reviewer.email
        template = request.repository.reviewer_review_status_change

    context = {
        'review': review,
        'status_text': status_text,
        'url': request.repository.site_url(path=reverse(
            'repository_review_detail',
            kwargs={
                'preprint_id': review.preprint.pk,
                'review_id': review.pk
            }
        ))
    }
    email_text = render_template.get_message_content(
        request,
        context,
        template,
        template_is_setting=True,
    )
    notify_helpers.send_email_with_body_from_user(
        request,
        '{} Review Invitation Status'.format(request.repository.object_name),
        to,
        email_text,
        log_dict=log_dict,
    )

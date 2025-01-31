from django.shortcuts import reverse

from utils import notify_helpers
from utils import models as utils_models


def send_typesetting_complete(**kwargs):
    request = kwargs['request']
    article = kwargs['article']

    description = 'Typesetting has been completed for article {0}.'.format(
        article.title)

    log_dict = {
        'level': 'Info', 'action_text': description,
        'types': 'Typesetting Complete',
        'actor': request.user,
        'target': article,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'typesetting_complete',
        'subject_typesetting_complete',
        article.editor_emails(),
        {'article': article},
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_proofreader_assign_notification(**kwargs):
    assignment = kwargs['assignment']
    request = kwargs['request']
    message = kwargs['message']
    skip = kwargs['skip']

    description = '{0} has been assigned as a proofreader for {1}'.format(
        assignment.proofreader.full_name(),
        assignment.round.article.title,
    )

    if not skip:
        log_dict = {
            'level': 'Info',
            'action_text': description,
            'types': 'Proofing Assignment',
            'target': assignment.round.article,
        }
        notify_helpers.send_email_with_body_from_user(
            request,
            'Proofing Request',
            assignment.proofreader.email,
            message,
            log_dict=log_dict,
        )
        notify_helpers.send_slack(
            request,
            description,
            ['slack_editors'],
        )
    else:
        utils_models.LogEntry.add_entry(
            types='Proofing Assignment',
            description=description,
            level='Info',
            request=request,
            target=assignment.round.article,
        )


def send_proofreader_assign_transaction_email(**kwargs):
    assignment = kwargs['assignment']
    request = kwargs['request']
    event_type = kwargs.get('event_type')

    description = '{user} has {action} the proofreading assignment for {article} assigned to {proofreader}'.format(
        user=request.user,
        action=event_type,
        article=assignment.round.article.title,
        proofreader=assignment.proofreader.full_name(),
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Proofreading Assignment {}'.format(event_type),
        'target': assignment.round.article,
    }

    if event_type in ['cancelled', 'reset']:
        message_target = assignment.proofreader.email
    else:
        message_target = assignment.manager.email

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'typesetting_proofreader_{}'.format(event_type),
        'Proofreader Assignment {}'.format(event_type),
        message_target,
        context={
            'assignment': assignment,
            'event_type': event_type,
        },
        log_dict=log_dict,
    )
    notify_helpers.send_slack(
        request,
        description,
        ['slack_editors'],
    )


def send_typesetting_assign_notification(**kwargs):
    assignment = kwargs['assignment']
    request = kwargs['request']
    skip = kwargs['skip']
    message = kwargs['message']

    description = '{0} has been assigned as a typesetter for {1}'.format(
        assignment.typesetter.full_name(),
        assignment.round.article.title,
    )

    if not skip:
        log_dict = {
            'level': 'Info',
            'action_text': description,
            'types': 'Typesetting Assignment',
            'target': assignment.round.article,
        }
        notify_helpers.send_email_with_body_from_user(
            request,
            'subject_typesetter_notification',
            assignment.typesetter.email,
            message,
            log_dict=log_dict,
        )
        notify_helpers.send_slack(
            request,
            description,
            ['slack_editors'],
        )
    else:
        utils_models.LogEntry.add_entry(
            types='Typesetting Assignment',
            description=description,
            level='Info',
            request=request,
            target=assignment.round.article,
        )


def send_typesetting_assign_decision(**kwargs):
    assignment = kwargs['assignment']
    request = kwargs['request']
    decision = kwargs['decision']
    note = kwargs['note']

    description = 'Typesetting task {0} decision made by {1}: {2}'.format(
        assignment.pk,
        assignment.typesetter.full_name(),
        decision,
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Typesetting Assignment Decision',
        'target': assignment.round.article,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'typsetting_typesetter_decision_{}'.format(decision),
        'Typesetting Assignment Decision',
        assignment.manager.email,
        context={'assignment': assignment, 'note': note},
        log_dict=log_dict,
    )

    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_typesetting_assign_cancelled(**kwargs):
    assignment = kwargs['assignment']
    request = kwargs['request']

    description = 'Typesetting task {0} cancelled by {1}'.format(
        assignment.pk,
        request.user,
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Typesetting Assignment Cancelled',
        'target': assignment.round.article,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'typesetting_typesetter_cancelled',
        'Typesetting Assignment Cancelled',
        assignment.typesetter.email,
        context={'assignment': assignment},
        log_dict=log_dict,
    )

    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_typesetting_assign_deleted(**kwargs):
    assignment = kwargs['assignment']
    request = kwargs['request']

    description = 'Typesetting task {0} deleted by {1}'.format(
        assignment.pk,
        request.user,
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Typesetting Assignment Deleted',
        'target': assignment.round.article,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'typesetting_typesetter_deleted',
        'Typesetting Assignment Deleted',
        assignment.typesetter.email,
        context={'assignment': assignment},
        log_dict=log_dict,
    )

    notify_helpers.send_slack(request, description, ['slack_editors'])


def send_typesetting_assign_complete(**kwargs):
    assignment = kwargs['assignment']
    article = assignment.round.article
    request = kwargs['request']
    url = request.journal.site_url(
        reverse("typesetting_article", kwargs={"article_id": article.pk})
    )

    description = 'Typesetting task completed by {0}'.format(
        assignment.typesetter.full_name(),
    )

    log_dict = {
        'level': 'Info',
        'action_text': description,
        'types': 'Typesetting Complete',
        'target': article,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request,
        'typesetting_typesetter_complete',
        'Typesetting Assignment Complete',
        assignment.manager.email,
        context={
            'assignment': assignment,
            'typesetting_article_url': url,
        },
        log_dict=log_dict,
    )

    notify_helpers.send_slack(request, description, ['slack_editors'])

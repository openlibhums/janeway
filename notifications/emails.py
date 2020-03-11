from utils import notify_helpers

from plugins.typesetting import models


def send_typesetting_complete(**kwargs):
    request = kwargs['request']
    article = kwargs['article']
    user_content_message = kwargs['user_content_message']
    assignment = kwargs['assignment']

    description = 'Typesetting has been completed for article {0}.'.format(
        article.title)

    log_dict = {
        'level': 'Info', 'action_text': description,
        'types': 'Typesetting Complete',
        'actor': request.user,
        'target': article,
    }

    notify_helpers.send_email_with_body_from_setting_template(
        request, 'typesetting_complete', 'subject_typesetting_complete',
        article.editor_emails(),
        {'article': article},
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ['slack_editors'])

from utils import models


def notify_hook(**kwargs):
    # dummy mock-up of new notification hook defer

    # action is a list of notification targets
    # if the "all" variable is passed, then some types of notification might act, like Slack.
    # Email, though, should only send if it's specifically an email in action, not on "all".
    action = kwargs.pop('action', [])

    if 'email_log' not in action:
        # email is only sent if list of actions includes "email"
        return

    # pop the args

    log_dict = kwargs.pop('log_dict', None)

    if log_dict:
        types = log_dict.get('types')
        action_text = log_dict.get('action_text')
        level = log_dict.get('level')
        request = kwargs.pop('request')
        target = log_dict.get('target')
        html = kwargs.pop('html')
        to = kwargs.pop('to')
        response = kwargs.pop('response')
        email_subject = kwargs.pop('email_subject')
        cc = kwargs.pop('cc')
        bcc = kwargs.pop('bcc')

        if hasattr(request, 'user'):
            actor = request.user
        else:
            actor = None

        if isinstance(response, dict):
            message_id = response['response'].get('id')
            models.LogEntry.add_entry(types=types, description=html, level=level,
                                      request=request, target=target, is_email=True, to=to,
                                      message_id=message_id, subject=action_text, actor=actor,
                                      email_subject=email_subject, cc=cc, bcc=bcc)
        else:
            models.LogEntry.add_entry(types=types, description=html, level=level, is_email=True,
                                      request=request, target=target, subject=action_text, to=to, actor=actor,
                                      email_subject=email_subject, cc=cc, bcc=bcc)


def plugin_loaded():
    pass

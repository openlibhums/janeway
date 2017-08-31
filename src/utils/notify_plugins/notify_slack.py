import json

from django.conf import settings

from utils.notify_plugins import notify_webhook
from utils import setting_handler


def notify_hook(**kwargs):
    # action is a list of notification targets
    # if the "all" variable is passed, then some types of notification might act, like Slack.
    # slack_message should be an appropriate object type for the webhook
    # request should be the current request
    action = kwargs.pop('action', [])

    if 'slack_editors' not in action and 'slack_admins' not in action and 'all' not in action:
        # slack responds to "all" and "slack_" commands
        return

    # pop the args
    slack_message = kwargs.pop('slack_message', '')
    slack_message = slack_message.replace('<br>', '\n').replace('<br />', '\n')
    request = kwargs.pop('request', None)

    if request and request.journal:
        if request.journal.slack_logging_enabled:
            try:
                slack_webhook = setting_handler.get_setting('general', 'slack_webhook', request.journal).value

                journal_name = request.journal.code

                # reformat the HTML into a slack-recognized format
                slack_message = {"text": u"[{0}] {1}".format(journal_name, slack_message), "icon_emoji": ":ghost:"}
                slack_json = json.dumps(slack_message)

                # call the method
                if 'slack_editors' in action:
                    notify_webhook.send_message(slack_webhook,
                                                slack_json, headers={'content-type': 'application/json'})

                if 'slack_admins' in action:
                    notify_webhook.send_message(slack_webhook,
                                                slack_json, headers={'content-type': 'application/json'})
            except IndexError:
                if settings.DEBUG:
                    print('There is no slack webhook registered for this journal.')
                else:
                    pass


def plugin_loaded():
    pass

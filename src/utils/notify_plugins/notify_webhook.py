import requests
import threading


def send_message(hook_url, message, headers=None):
    # this sends a non-blocking post to a web URL
    hook_thread = threading.Thread(target=requests.post, args=(hook_url, message, headers), kwargs={})
    hook_thread.start()


def notify_hook(**kwargs):
    # action is a list of notification targets
    # if the "all" variable is passed, then some types of notification might act, like Slack.
    # url should be passed here for where to send the webhook
    # html should be an appropriate object type for the webhook
    # headers should be a dictionary of headers

    action = kwargs.pop('action', [])

    if 'webhook' not in action:
        return

    # pop the args
    html = kwargs.pop('html', '')
    url = kwargs.pop('url', '')
    headers = kwargs.pop('headers', '')

    send_message(url, html, headers)


def plugin_loaded():
    pass

import requests
import threading

from utils.logger import get_logger

logger = get_logger(__name__)


def _post_and_check(url, data, headers):
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
    except requests.RequestException as error:
        logger.error("Webhook POST to %s failed: %s", url, error)


def send_message(hook_url, message, headers=None):
    # Fire and forget call to avoid blocking
    # TODO: use a queue and worker
    hook_thread = threading.Thread(
        target=_post_and_check, args=(hook_url, message, headers or {})
    )
    hook_thread.start()


def notify_hook(**kwargs):
    # action is a list of notification targets
    # if the "all" variable is passed, then some types of notification might act, like Slack.
    # url should be passed here for where to send the webhook
    # html should be an appropriate object type for the webhook
    # headers should be a dictionary of headers

    action = kwargs.pop("action", [])

    if "webhook" not in action:
        return

    # pop the args
    html = kwargs.pop("html", "")
    url = kwargs.pop("url", "")
    headers = kwargs.pop("headers", "")

    send_message(url, html, headers)


def plugin_loaded():
    pass

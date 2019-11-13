from utils import setting_handler

from core.homepage_elements.featured import plugin_settings


def get_popular_article_settings(journal):
    plugin = plugin_settings.get_self()

    try:
        most_downloaded = setting_handler.get_plugin_setting(
            plugin,
            'most_downloaded',
            journal,
        ).value
    except IndexError:
        most_downloaded = False

    try:
        num_most_downloaded = setting_handler.get_plugin_setting(
            plugin,
            'num_most_downloaded',
            journal,
        ).value
    except IndexError:
        num_most_downloaded = 0
    try:
        most_downloaded_time = setting_handler.get_plugin_setting(
            plugin,
            'most_downloaded_time',
            journal,
        ).value
    except IndexError:
        most_downloaded_time = 'weekly'

    return most_downloaded, num_most_downloaded, most_downloaded_time

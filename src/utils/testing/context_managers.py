from contextlib import contextmanager

from utils import setting_handler


@contextmanager
def janeway_setting_override(setting_group, setting_name, journal=None, value=None):
    prev_value = setting_handler.get_setting(
        setting_group,
        setting_name,
        journal=journal,
    ).value
    try:
        setting_handler.save_setting(
            setting_group,
            setting_name,
            journal=journal,
            value=value,
        )
        yield
    finally:
        setting_handler.save_setting(
            setting_group,
            setting_name,
            journal=journal,
            value=prev_value,
        )

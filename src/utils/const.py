from enum import Enum, EnumMeta
from bleach_allowlist import (
    all_styles as _all_styles,
    generally_xss_safe as _generally_xss_safe
)

class EnumContainsMeta(EnumMeta):

    def __contains__(cls, value):
        try:
            cls(value)
        except ValueError:
            return False
        return True

class EnumContains(Enum, metaclass=EnumContainsMeta):
    pass


def get_allowed_html_tags():
    return _generally_xss_safe


def get_allowed_css_styles():
    return _all_styles

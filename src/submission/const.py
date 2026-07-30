"""
Constants defined by the submission app
"""

from utils.const import EnumContains


class AddAuthorStatus(EnumContains):
    OK = "ok"
    NOT_FOUND = "not_found"
    ORCID_ERROR = "orcid_error"

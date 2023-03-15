"""
Constants defined by the review app
"""
from utils.const import EnumContains


class EditorialDecisions(EnumContains):
    ACCEPT = 'accept'
    DECLINE = 'decline'
    UNDECLINE = 'undecline'
    MINOR_REVISIONS = 'minor_revisions'
    MAJOR_REVISIONS = 'major_revisions'

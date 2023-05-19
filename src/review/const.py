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


class ReviewerDecisions(EnumContains):
    DECISION_ACCEPT = 'accept'
    DECISION_MINOR = 'minor_revisions'
    DECISION_MAJOR = 'major_revisions'
    DECISION_REJECT = 'reject'
    DECISION_NO_RECOMMENDATION = 'none'
    DECISION_WITHDRAWN = 'withdrawn'

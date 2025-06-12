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
    CONDITIONAL_ACCEPT = 'conditional_accept'
    REVIEW = 'review'


class ReviewerDecisions(EnumContains):
    DECISION_ACCEPT = 'accept'
    DECISION_MINOR = 'minor_revisions'
    DECISION_MAJOR = 'major_revisions'
    DECISION_REJECT = 'reject'
    DECISION_NO_RECOMMENDATION = 'none'
    DECISION_WITHDRAWN = 'withdrawn'


class VisibilityOptions(EnumContains):
    OPEN = 'open'
    SINGLE_ANON = 'blind'
    DOUBLE_ANON = 'double-blind'

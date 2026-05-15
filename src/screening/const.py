"""
Constants defined by the screening app.

The recommendation vocabulary is intentionally softer than peer review's
per the ILR specification in bau#271 — editorial teams asked for language
that does not feel as harsh to authors when their submission is being
filtered before peer review.
"""

from utils.const import EnumContains


class ScreeningRecommendations(EnumContains):
    """Recommendations a screener may make on a submission."""

    ACCEPT_FOR_PEER_REVIEW = "accept_for_peer_review"
    REVISIONS_REQUIRED = "revisions_required"
    DECLINE = "decline"
    NO_RECOMMENDATION = "no_recommendation"
    WITHDRAWN = "withdrawn"


class ScreeningRevisionTypes(EnumContains):
    """Revision types that can be requested following screening."""

    MINOR_REVISIONS = "minor_revisions"
    MAJOR_REVISIONS = "major_revisions"


def screener_recommendation_choices():
    return (
        (None, "-----------"),
        (
            ScreeningRecommendations.ACCEPT_FOR_PEER_REVIEW.value,
            "Accept for Peer Review",
        ),
        (
            ScreeningRecommendations.REVISIONS_REQUIRED.value,
            "Revisions Required",
        ),
        (ScreeningRecommendations.DECLINE.value, "Decline"),
    )


def all_screener_recommendations():
    return (
        (
            ScreeningRecommendations.ACCEPT_FOR_PEER_REVIEW.value,
            "Accept for Peer Review",
        ),
        (
            ScreeningRecommendations.REVISIONS_REQUIRED.value,
            "Revisions Required",
        ),
        (ScreeningRecommendations.DECLINE.value, "Decline"),
        (
            ScreeningRecommendations.NO_RECOMMENDATION.value,
            "No Recommendation",
        ),
        (
            ScreeningRecommendations.WITHDRAWN.value,
            "Withdrawn",
        ),
    )


def screening_revision_type_choices():
    return (
        (ScreeningRevisionTypes.MINOR_REVISIONS.value, "Minor Revisions"),
        (ScreeningRevisionTypes.MAJOR_REVISIONS.value, "Major Revisions"),
    )

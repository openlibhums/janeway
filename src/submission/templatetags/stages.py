from django import template

from journal.models import Issue
from submission import models

register = template.Library()


@register.simple_tag
def in_stage_group(attribute, stage_group):
    """
    Checks if the attribute passed is in a stage group.
    :param attribute: string, name of a stage
    :param stage_group: string, name of a group
    :return: boolean
    """

    if stage_group == 'review':
        stages = models.REVIEW_STAGES
    elif stage_group == 'copyediting':
        stages = models.COPYEDITING_STAGES
    elif stage_group == 'preprint':
        stages = models.PREPRINT_STAGES
    else:
        stages = []

    if stages and attribute in stages:
        return True

    return False


@register.simple_tag
def select_issue_available(journal, user):
    """
    Checks if the user can select an issue for the article.

    Selectable issues are ones open for submission, for the current journal, to which the user has been invited (if
    submission is by invitation only).

    :param journal: Journal
    :param user: User
    :return: boolean
    """

    return Issue.objects.by_user(user).open_for_submission().current_journal(journal).exists()
from django import template

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



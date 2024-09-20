from django import template

from core import models
from core.middleware import GlobalRequestMiddleware
from submission import models
from utils import setting_handler

register = template.Library()


@register.simple_tag()
def user_has_role(request, role, staff_override=True):
    if not request.user.is_authenticated:
        return None
    return request.user.check_role(
        request.journal,
        role,
        staff_override=staff_override
    )


@register.simple_tag
def user_roles(journal, user, slugs=False):
    if slugs:
        return [
            ar.role.slug
            for ar in models.AccountRole.objects.filter(
                user=user, journal=journal
            )
        ]
    else:
        return [
            ar
            for ar in models.AccountRole.objects.filter(
                user=user, journal=journal
            )
        ]


@register.simple_tag
def role_users(request, role_slug):
    role_holders = models.AccountRole.objects.filter(role__slug=role_slug)
    return [holder.user for holder in role_holders]


@register.simple_tag
def role_id(request, role_slug):
    try:
        role = models.Role.objects.get(slug=role_slug)
        return role.pk
    except models.Role.DoesNotExist:
        return 0


@register.filter
def se_can_see_pii(value, article):
    # Before doing anything, check the setting is enabled:
    se_pii_filter_enabled = setting_handler.get_setting(
        setting_group_name='permission',
        setting_name='se_pii_filter',
        journal=article.journal,
    ).processed_value

    if not se_pii_filter_enabled:
        return value

    # Check if the user is an SE and return an anonymised value.
    # If the user is not a section editor we assume they have permission
    # to view the actual value.
    request = GlobalRequestMiddleware.get_current_request()
    stages = [
        models.STAGE_UNASSIGNED,
        models.STAGE_UNDER_REVIEW,
        models.STAGE_UNDER_REVISION,
    ]
    if request.user in article.section_editors() and article.stage in stages:
        return 'Value Anonymised'
    else:
        return value

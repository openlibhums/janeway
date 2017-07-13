from django import template

register = template.Library()


@register.simple_tag()
def user_has_role(request, role):
    return request.user.check_role(request.journal, role)

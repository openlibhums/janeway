from django import template

register = template.Library()


@register.filter('startswith')
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False

@register.filter
def concat(original, added):
    return str(original) + str(added)

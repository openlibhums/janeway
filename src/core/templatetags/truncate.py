from django import template

register = template.Library()


@register.filter
def truncatesmart(value, limit=80):
    """
    Truncates strings keeping whole words. Usage:

    {% load truncate %}

    {{ string|truncatesmart }}
    {{ string|truncatesmart:100 }}
    """

    try:
        limit = int(limit)
    except ValueError:
        return value

    if len(value) <= limit:
        return value

    value = value[:limit]
    words = value.split(' ')[:-1]

    return ' '.join(words) + ' [...]'

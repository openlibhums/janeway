from django import template
from uuid import uuid4

register = template.Library()

@register.simple_tag
def short_uuid4():
    return f'u{str(uuid4())[:8]}'

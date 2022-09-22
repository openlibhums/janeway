from nose import tools
from django import template

register = template.Library()

class NoseNode(template.Node):

    def render(self, context):
        tools.set_trace()         # Debugger will stop here
        return ''

@register.tag
def set_trace(parser, token):
    return NoseNode()

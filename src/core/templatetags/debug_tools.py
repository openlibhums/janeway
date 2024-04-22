from django import template
from utils.logger import get_logger

logger = get_logger(__name__)

register = template.Library()


class TraceNode(template.Node):
    """
    Allows you to set a trace inside a template.
    Usage:
    {% load debug_tools %}
    ...
    {% set_trace %}
    """

    def render(self, context):
        import pdb
        pdb.set_trace()
        return ''


@register.tag
def set_trace(parser, token):
    return TraceNode()

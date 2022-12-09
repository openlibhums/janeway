from django import template

import markdown

register = template.Library()


@register.filter
def markdown_to_html(markdown_text):
    """
    Returns HTML from Markdown input

    {% load markdown %}

    {{ markdown_variable|markdown_to_html }}
    """
    return markdown.markdown(markdown_text)

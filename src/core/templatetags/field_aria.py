"""
Template tag for rendering a single bound form field with extra ARIA
attributes that its widget wasn't given at the Python level - e.g. an
aria-describedby that only makes sense once a theme template knows the id
of a label it's about to render alongside the field.
"""

from django import template

register = template.Library()


@register.simple_tag
def field_aria(field, label=None, labelledby=None, describedby=None, css_class=""):
    """Render a bound field with aria-label/-labelledby/-describedby (and
    optionally a CSS class) merged onto its widget, without altering the
    field itself.

    :field: a django.forms.BoundField
    :label: value for aria-label
    :labelledby: value for aria-labelledby
    :describedby: value for aria-describedby
    :css_class: optional value for the widget's class attribute
    """
    attrs = {}
    if label:
        attrs["aria-label"] = label
    if labelledby:
        attrs["aria-labelledby"] = labelledby
    if describedby:
        attrs["aria-describedby"] = describedby
    if css_class:
        attrs["class"] = css_class
    return field.as_widget(attrs=attrs)

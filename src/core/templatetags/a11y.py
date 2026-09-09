from django import template

register = template.Library()


@register.filter
def field_describedby(field, include_helptext=True):
    """
    Render a bound field's widget with aria-describedby pointing at its
    error/help-text ids, since {{ field }} can't take an attrs kwarg.

    :param field: A BoundField
    :param include_helptext: pass False for templates that don't render
        the help-text block for this field (e.g. the inline branch of
        foundationform/_foundation_form_field.html), so a dangling id
        isn't referenced
    :return: Safe HTML widget markup, with aria-describedby set if the
        field has errors and/or help text, unchanged otherwise
    """
    ids = ["%s_error_%d" % (field.auto_id, i) for i in range(1, len(field.errors) + 1)]
    if include_helptext and field.help_text:
        ids.append("%s_helptext" % field.auto_id)
    if not ids:
        return field
    return field.as_widget(attrs={"aria-describedby": " ".join(ids)})

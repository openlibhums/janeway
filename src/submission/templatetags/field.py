import types
from django import template

register = template.Library()


@register.simple_tag
def get_form_field(form, field_name):
    return form.__getitem__(field_name)


@register.filter(name="form_id")
def form_id(field, id=None):
    """ Given a django form field, sets the form id attribute
    Useful for HTML compliant forms used with table rows
    :param field: A django forms.Field
    :param id: A str that represents a form id. If one is present, new parts
        are chained together
    """
    import types
    orig_as_widget = field.as_widget

    def as_widget(self, *args, **kwargs):
        attrs = kwargs.pop("attrs", {})
        attrs["form"] = str(id) + attrs.get("form", "")
        kwargs["attrs"] = attrs
        html = orig_as_widget(*args, **kwargs)
        self.as_widget = orig_as_widget  # return to original state
        return html

    field.as_widget = types.MethodType(as_widget, field)
    return field

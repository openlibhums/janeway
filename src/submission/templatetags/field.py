from django import template

register = template.Library()


@register.simple_tag
def get_form_field(form, field_name):
    return form.__getitem__(field_name)

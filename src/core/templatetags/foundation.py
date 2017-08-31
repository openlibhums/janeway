from django.template.loader import get_template
from django.template import Library


register = Library()


def get_context_template(element):
    element_type = element.__class__.__name__.lower()

    if element_type == 'boundfield':
        template = get_template("foundationform/_foundation_form_field.html")
        context = {'field': element}
    else:
        if hasattr(element, 'management_form'):
            template = get_template("foundationform/foundation_formset.html")
            context = {'formset': element}
        else:
            template = get_template("foundationform/foundation_form.html")
            context = {'form': element}
    return template, context


@register.filter
def foundation(element):
    template, context = get_context_template(element)
    return template.render(context)


@register.filter
def foundationinline(element):
    template, context = get_context_template(element)
    context['inline'] = True
    return template.render(context)

"""
Template tag for re-scoping a form's field ids when the same bound form is
rendered more than once on one page (e.g. a mobile/desktop pair of the same
filter form) - without it, every field would render with the same id/for
pair in both copies, which is invalid HTML and leaves label association
pointing at whichever copy happens to come first in the DOM.
"""

from django import template

register = template.Library()


@register.simple_tag
def set_auto_id(form, auto_id):
    """Set a form's auto_id template (e.g. "id_%s-desktop"), so every field
    rendered from this point on gets an id/label scoped to that copy.

    Mutates the form in place and renders nothing. Call this once before
    rendering each copy of a form that appears more than once on a page.

    :form: a django.forms.Form (or subclass) instance
    :auto_id: the auto_id template to use, e.g. "id_%s-desktop"
    """
    form.auto_id = auto_id
    return ""

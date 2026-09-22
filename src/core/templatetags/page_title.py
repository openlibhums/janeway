from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def page_title(context, *segments):
    """
    Build a page title in the form "<site name> | <segment> | <segment> ...".

    The site name is the current journal, repository, or press name,
    picked from the request in that priority order. Falsy segments
    are dropped, so a page can be titled with just the site name by
    passing no segments at all.

    :param context: template context, used to read the request
    :param segments: additional title segments, most general first
    :return: the assembled title string
    """
    request = context.get("request")
    site_name = ""
    if request:
        if getattr(request, "journal", None):
            site_name = request.journal.name
        elif getattr(request, "repository", None):
            site_name = request.repository.name
        elif getattr(request, "press", None):
            site_name = request.press.name

    parts = [site_name] + [str(segment).strip() for segment in segments if segment]
    return " | ".join(part for part in parts if part)

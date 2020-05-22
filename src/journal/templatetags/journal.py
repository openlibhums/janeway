from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def current_journal(context, queryset):
    """
    Takes a queryset and filters it by the current journal.
    :param context: View context
    :param queryset: A queryset with a journal FK
    :return: a queryset
    """
    request = context.get('request')

    if not request.journal:
        return queryset

    return queryset.filter(journal=request.journal)


@register.simple_tag(takes_context=True)
def current_journal_count(context, queryset):
    """
    Takes a queryset and filters it by the current journal and returns a count.
    :param context: View context
    :param queryset: A queryset with a journal FK
    :return: an integer
    """
    request = context.get('request')

    if not request.journal:
        return queryset

    return queryset.filter(journal=request.journal).count()

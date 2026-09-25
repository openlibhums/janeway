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
    request = context.get("request")

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
    request = context.get("request")

    if not request.journal:
        return queryset

    return queryset.filter(journal=request.journal).count()


@register.filter
def group_issue_articles(articles, grouping):
    """
    Groups issue articles for display, see journal.logic.group_issue_articles
    :param articles: articles sorted with Issue.get_sorted_articles
    :param grouping: one of journal.models.ARTICLE_GROUPING_CHOICES
    :return: a list of journal.logic.ArticleGroup
    """
    from journal import logic  # Avoids circular import

    return logic.group_issue_articles(articles, grouping)


@register.filter
def issue_article_label(article, grouping):
    """
    Returns the label displayed above an article title in an issue,
    see journal.logic.issue_article_label
    :param article: an Article object
    :param grouping: one of journal.models.ARTICLE_GROUPING_CHOICES
    :return: a string
    """
    from journal import logic  # Avoids circular import

    return logic.issue_article_label(article, grouping)

from django import template

register = template.Library()


@register.simple_tag()
def article_active_user_review(request, article):
    return article.active_review_request_for_user(request.user)

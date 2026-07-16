from django import template
from django.urls import reverse

from repository import models as repo_models
from submission import models as submission_models

register = template.Library()

ARTICLE_VIEW_NAMES = {
    "article_view",
    "article_view_custom_identifier",
    "article_print_article",
}

NEWS_ITEM_VIEW_NAMES = {"core_news_item"}

PREPRINT_VIEW_NAMES = {"repository_preprint", "repository_pdf"}

HOME_VIEW = "website_index"


def press_sitemap_url(press):
    return f"{press.site_url()}/sitemap.xml"


def press_pages_sitemap_url(press):
    return f"{press.site_url()}/pages_sitemap.xml"


def press_news_sitemap_url(press):
    return f"{press.site_url()}/news_sitemap.xml"


def journal_sitemap_url(journal):
    return f"{journal.site_url()}/sitemap.xml"


def journal_pages_sitemap_url(journal):
    return f"{journal.site_url()}/pages_sitemap.xml"


def journal_news_sitemap_url(journal):
    return f"{journal.site_url()}/news_sitemap.xml"


def issue_sitemap_url(journal, issue):
    path = reverse("journal_sitemap", kwargs={"issue_id": issue.pk})
    return journal.site_url(path=path)


def no_issue_sitemap_url(journal):
    path = reverse("journal_no_issue_sitemap")
    return journal.site_url(path=path)


def repo_sitemap_url(repo):
    return f"{repo.site_url()}/sitemap.xml"


def repo_pages_sitemap_url(repo):
    return f"{repo.site_url()}/pages_sitemap.xml"


def subject_sitemap_url(repo, subject):
    path = reverse("repository_sitemap", kwargs={"subject_id": subject.pk})
    return repo.site_url(path=path)


def no_subject_sitemap_url(repo):
    path = reverse("repository_no_subject_sitemap")
    return repo.site_url(path=path)


@register.simple_tag(takes_context=True)
def page_sitemap_url(context, view_name, obj=None):
    """Return the most specific sitemap URL for the current page.

    Usage:
        {% load sitemap_tags %}
        {% page_sitemap_url request.resolver_match.url_name %}
        {% page_sitemap_url request.resolver_match.url_name article %}
        {% page_sitemap_url request.resolver_match.url_name preprint %}
    """
    request = context.get("request")
    if request is None:
        return ""

    # Fall back to the page's primary object in context so the article/preprint
    # branches work on every theme, even footers that don't pass an object.
    if obj is None:
        if view_name in ARTICLE_VIEW_NAMES:
            obj = context.get("article")
        elif view_name in PREPRINT_VIEW_NAMES:
            obj = context.get("preprint")

    if request.repository:
        return resolve_repo_sitemap_url(request.repository, view_name, obj)
    if request.journal:
        return resolve_journal_sitemap_url(request.journal, view_name, obj)
    return resolve_press_sitemap_url(request.press, view_name, obj)


def resolve_press_sitemap_url(press, view_name, obj):
    if view_name == HOME_VIEW:
        return press_sitemap_url(press)
    if view_name in NEWS_ITEM_VIEW_NAMES:
        return press_news_sitemap_url(press)
    return press_pages_sitemap_url(press)


def resolve_journal_sitemap_url(journal, view_name, obj):
    if view_name == HOME_VIEW:
        return journal_sitemap_url(journal)
    if view_name in NEWS_ITEM_VIEW_NAMES:
        return journal_news_sitemap_url(journal)
    if view_name in ARTICLE_VIEW_NAMES and isinstance(obj, submission_models.Article):
        # Use the same canonical regular issue the article is listed under, so
        # the footer points to the one issue sub-sitemap that contains it.
        from utils.logic import canonical_issue

        issue = canonical_issue(obj)
        if issue is not None:
            return issue_sitemap_url(journal, issue)
        return no_issue_sitemap_url(journal)
    return journal_pages_sitemap_url(journal)


def resolve_repo_sitemap_url(repo, view_name, obj):
    if view_name == HOME_VIEW:
        return repo_sitemap_url(repo)
    if view_name in PREPRINT_VIEW_NAMES and isinstance(obj, repo_models.Preprint):
        if obj.subject.exists():
            first_subject = obj.subject.order_by("name").first()
            return subject_sitemap_url(repo, first_subject)
        return no_subject_sitemap_url(repo)
    return repo_pages_sitemap_url(repo)

from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from journal import forms, logic, models
from security.decorators import editor_user_required
from submission import models as submission_models
from utils.htmx import hx_show_message


@require_GET
@editor_user_required
def issue_toc_article_row(request, issue_id, article_id):
    """
    Renders an article of the issue table of contents as a table row.
    :param request: HttpRequest object
    :param issue_id: Issue object PK
    :param article_id: Article object PK
    :return: HttpResponse
    """
    issue, article = logic.get_issue_article(request, issue_id, article_id)
    template = "admin/journal/partials/issue_toc/article_row.html"
    context = {"issue": issue, "article": article}
    return render(request, template, context)


@require_http_methods(["GET", "POST"])
@editor_user_required
def issue_toc_article_edit(request, issue_id, article_id):
    """
    Edits the section and topic of an article of the issue table of contents.
    GET renders the row as a form, POST saves it and renders the whole table
    of contents, since the article may have moved to another group.
    :param request: HttpRequest object
    :param issue_id: Issue object PK
    :param article_id: Article object PK
    :return: HttpResponse
    """
    issue, article = logic.get_issue_article(request, issue_id, article_id)
    form = forms.IssueArticleGroupingForm(instance=article)

    if request.method == "POST":
        form = forms.IssueArticleGroupingForm(request.POST, instance=article)
        if form.is_valid():
            article = form.save()
            if "section" in form.changed_data:
                # Orderings are stored per section. Keep one per issue,
                # preferring the new section's, so the update can't collide.
                orderings = models.ArticleOrdering.objects.filter(article=article)
                kept = {}
                for ordering in orderings:
                    if (
                        ordering.issue_id not in kept
                        or ordering.section_id == article.section_id
                    ):
                        kept[ordering.issue_id] = ordering.pk
                orderings.exclude(pk__in=kept.values()).delete()
                orderings.update(section=article.section)
            response = logic.issue_toc_response(request, issue)
            return hx_show_message(
                response,
                _("Updated the section and topic of %(title)s.")
                % {"title": article.safe_title},
            )

    template = "admin/journal/partials/issue_toc/article_edit_row.html"
    context = {"issue": issue, "article": article, "form": form}
    response = render(request, template, context)
    if request.method == "POST":
        # The confirm button targets the table of contents
        response["HX-Retarget"] = "#articles-{}".format(article.pk)
        response["HX-Reswap"] = "outerHTML"
    return response


@require_POST
@editor_user_required
def sort_issue_sections(request, issue_id):
    """
    Moves a section before or after another in the table of contents.
    :param request: HttpRequest object
    :param issue_id: Issue object PK
    :return: HttpResponse or HttpRedirect
    """
    issue = get_object_or_404(models.Issue, pk=issue_id, journal=request.journal)
    sections = list(issue.get_sorted_sections())
    target = logic.get_move_target(request, submission_models.Section, sections)
    if target:
        issue.set_section_order(logic.move_in_order(sections, *target))

    return logic.issue_toc_response(request, issue)


@require_POST
@editor_user_required
def sort_issue_topics(request, issue_id):
    """
    Moves a topic before or after another in the table of contents.
    :param request: HttpRequest object
    :param issue_id: Issue object PK
    :return: HttpResponse or HttpRedirect
    """
    issue = get_object_or_404(models.Issue, pk=issue_id, journal=request.journal)
    topics = list(issue.all_topics)
    target = logic.get_move_target(request, models.Topic, topics)
    if target:
        issue.set_topic_order(logic.move_in_order(topics, *target))

    return logic.issue_toc_response(request, issue)

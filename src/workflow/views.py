from django.shortcuts import render
from django.shortcuts import get_object_or_404

from security.decorators import editor_user_required, has_journal
from submission import models as submission_models


@has_journal
@editor_user_required
def manage_article_workflow(request, article_id):
    """
    Presents an interface for an Editor user to move an article back along its workflow.
    :param request: HttpRequest object
    :param article_id: Article pbject PK
    :return: HttpResponse or HttpRedirect
    """

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal
    )

    template = 'workflow/manage_article_workflow.html'
    context = {
        'article': article,
    }

    return render(request, template, context)




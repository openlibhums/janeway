__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.http import HttpResponse
from django.shortcuts import reverse, get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.http import require_POST

from identifiers import models, forms
from submission import models as submission_models
from utils import models as util_models
from security.decorators import production_user_or_editor_required


def pingback(request):
    # TODO: not sure what Crossref will actually
    #  send here so for now it just dumps all data

    output = ''

    for key, value in request.POST.items():
        output += '{0}: {1}\n'.format(key, value)

    util_models.LogEntry.add_entry(
        'Submission',
        "Response from Crossref pingback: {0}".format(output),
        'Info',
    )

    return HttpResponse('')


@production_user_or_editor_required
def article_identifiers(request, article_id):
    """
    Displays a list of current article identifiers.
    :param request: HttpRequest
    :param article_id: Article object PK
    :return: HttpResponse
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    identifiers = models.Identifier.objects.filter(article=article)

    template = 'identifiers/article_identifiers.html'
    context = {
        'article': article,
        'identifiers': identifiers,
    }

    return render(request, template, context)


@production_user_or_editor_required
def manage_identifier(request, article_id, identifier_id=None):
    """
    Allows an editor to add a new or edit and existing identifier.
    :param request: HttpRequest
    :param article_id: Article object PK
    :param identifier_id: Identifier object PK, optional
    :return: HttpResponse or Redirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    identifier = get_object_or_404(
        models.Identifier,
        pk=identifier_id,
        article=article,
    ) if identifier_id else None

    form = forms.IdentifierForm(instance=identifier)

    if request.POST:
        form = forms.IdentifierForm(request.POST, instance=identifier)

        if form.is_valid():
            form.save(article=article)
            messages.add_message(
                request,
                messages.SUCCESS,
                "Identifier saved.",
            )
            return redirect(
                reverse(
                    'article_identifiers',
                    kwargs={'article_id': article.pk},
                )
            )

    template = 'identifiers/manage_identifier.html'
    context = {
        'article': article,
        'identifier': identifier,
        'form': form,
    }

    return render(request, template, context)


@require_POST
@production_user_or_editor_required
def issue_doi(request, article_id, identifier_id):
    """
    Issues a DOI identifier
    :param request: HttpRequest
    :param article_id: Article object PK
    :param identifier_id: Identifier object PK
    :return: HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    identifier = get_object_or_404(
        models.Identifier,
        pk=identifier_id,
        article=article,
        id_type='doi',
    )

    status, error = identifier.register()
    messages.add_message(
        request,
        messages.INFO if not error else messages.ERROR,
        status
    )

    return redirect(
        reverse(
            'article_identifiers',
            kwargs={'article_id': article.pk},
        )
    )


@require_POST
@production_user_or_editor_required
def delete_identifier(request, article_id, identifier_id):
    """
    Deletes an identifier
    :param request: HttpRequest
    :param article_id: Article object PK
    :param identifier_id: Identifier object PK
    :return: HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    identifier = get_object_or_404(
        models.Identifier,
        pk=identifier_id,
        article=article,
    )

    identifier.delete()
    messages.add_message(
        request, messages.SUCCESS,
        'Identifier deleted.'
    )

    return redirect(
        reverse(
            'article_identifiers',
            kwargs={'article_id': article.pk},
        )
    )

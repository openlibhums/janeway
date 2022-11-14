__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.http import HttpResponse
from django.shortcuts import reverse, get_object_or_404, redirect, render, render_to_response
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.db.models import OuterRef, Subquery

from identifiers import models, forms
from submission import models as submission_models
from core import views as core_views
from journal import models as journal_models

from security.decorators import production_user_or_editor_required, editor_user_required
from identifiers import logic

import datetime
from uuid import uuid4

from django.urls import reverse
from django.contrib import messages
from django.utils import timezone


from utils import models as util_models


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

    form = forms.IdentifierForm(
        instance=identifier,
        article=article,
    )

    if request.POST:
        form = forms.IdentifierForm(
            request.POST,
            instance=identifier,
            article=article,
        )

        if form.is_valid():
            form.save()
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


@production_user_or_editor_required
def show_doi(request, article_id, identifier_id):
    """
    Shows a DOI deposit
    :param request: HttpRequest
    :param article_id: Article object PK
    :param identifier_id: Identifier object PK
    :return: HttpRedirect
    """
    from utils import setting_handler
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

    try:
        document = identifier.crossrefstatus.latest_deposit.document
        if not document:
            raise AttributeError
        return HttpResponse(document, content_type="application/xml")
    except AttributeError:
        template_context = logic.create_crossref_doi_batch_context(request.journal, set([identifier]))
        template = 'common/identifiers/crossref_doi_batch.xml'
        return render_to_response(template, template_context, content_type="application/xml")


@production_user_or_editor_required
def poll_doi(request, article_id, identifier_id):
    """
    Polls crossref for DOI info
    :param request: HttpRequest
    :param article_id: Article object PK
    :param identifier_id: Identifier object PK
    :return: HttpRedirect
    """
    from utils import setting_handler
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

    # Scenario 1: The identifier has not been polled or deposited before.
    # It needs a CrossrefStatus object created.
    if not identifier.crossrefstatus:
        models.CrossrefStatus.objects.create(identifier=identifier)

    # Scenario 2: The identifier has been deposited before.
    # It will have a CrossrefStatus and a CrossrefDeposit already.
    elif identifier.crossrefstatus.latest_deposit:
        status, error = identifier.crossrefstatus.latest_deposit.poll()
        messages.add_message(
            request,
            messages.INFO if not error else messages.ERROR,
            status
        )

    # Scenario 3: The identifier has only been polled before
    # but not deposited. It will have a CrossrefStatus already,
    # but no CrossrefDeposit. This is OK, and the status should be
    # updated and returned on this basis.

    # In all scenarios, update the CrossrefStatus last.
    identifier.crossrefstatus.update()

    return redirect(
        reverse(
            'article_identifiers',
            kwargs={'article_id': article.pk},
        )
    )


@production_user_or_editor_required
def poll_doi_output(request, article_id, identifier_id):
    """
    Gets Crossref response stored on CrossrefDeposit
    :param request: HttpRequest
    :param article_id: Article object PK
    :param identifier_id: Identifier object PK
    :return: HttpRedirect
    """
    from utils import setting_handler
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

    if not identifier.crossrefstatus:
        return HttpResponse('Error: no deposit found')
    elif 'doi_batch' not in identifier.crossrefstatus.latest_deposit.result_text:
        return HttpResponse(identifier.crossrefstatus.latest_deposit.result_text)
    else:
        text = identifier.crossrefstatus.latest_deposit.get_record_diagnostic(identifier.identifier)
        if text:
            resp = HttpResponse(text, content_type="application/xml")
        else:
            resp = HttpResponse(identifier.crossrefstatus.latest_deposit.result_text, content_type="application/xml")
        resp['Content-Disposition'] = 'inline;'
        return resp


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


@method_decorator(editor_user_required, name='dispatch')
class IdentifierManager(core_views.FilteredArticlesListView):
    template_name = 'core/manager/identifier_manager.html'

    # None or integer
    action_queryset_chunk_size = 100

    def get_facets(self):

        crossref_status_obj = models.CrossrefStatus.objects.filter(
            identifier__article=OuterRef('pk'),
        )

        status = Subquery(
            crossref_status_obj.values('message')[:1]
        )

        facets = {
            'date_published__gte': {
                'type': 'date_time',
                'field_label': 'Pub date from',
            },
            'date_published__lte': {
                'type': 'date_time',
                'field_label': 'Pub date to',
            },
            'status': {
                'type': 'charfield_with_choices',
                'annotations': {
                    'status': status,
                },
                'model_choices': models.CrossrefStatus._meta.get_field('message').choices,
                'field_label': 'Status',
            },
            'journal__pk': {
                'type': 'foreign_key',
                'model': journal_models.Journal,
                'field_label': 'Journal',
                'choice_label_field': 'name',
            },
            'primary_issue__pk': {
                'type': 'foreign_key',
                'model': journal_models.Issue,
                'field_label': 'Primary issue',
                'choice_label_field': 'display_title',
            },
        }
        return self.filter_facets_if_journal(facets)

    def get_actions(self):
        return [
            {
                'name': 'register_dois',
                'value': 'Register DOIs',
                'action': logic.register_batch_of_crossref_dois,
            },
            {
                'name': 'poll_doi_status',
                'value': 'Poll for status',
                'action': logic.poll_dois_for_articles,
            },
        ]

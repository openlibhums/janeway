import time
import uuid
import datetime

from django.db import transaction
from django.db.models import Q, ExpressionWrapper, BooleanField
from django.shortcuts import redirect, reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from core import models as core_models, files
from events import logic as event_logic
from identifiers import logic as ident_logic
from identifiers.models import DOI_RE
from production import logic
from utils import setting_handler, render_template

from typesetting import models
from typesetting.notifications import notify


def production_ready_files(article, file_objects=False):
    """
    Deprecated.
    Gathers a list of production ready files.
    :param article: an Article object
    :param file_objects: Boolean
    :return: a list of File type objects
    """
    raise DeprecationWarning('Use get_typesetting_files instead.')
    submitted_ms_files = article.manuscript_files.filter(is_galley=False)
    copyeditted_files = logic.get_copyedit_files(article)

    if file_objects:
        file_pks = list()

        for file in submitted_ms_files:
            file_pks.append(file.pk)

        for file in copyeditted_files:
            file_pks.append(file.pk)

        return core_models.File.objects.filter(pk__in=file_pks)

    else:

        return {
            'Manuscript File': submitted_ms_files,
            'Copyedited File': copyeditted_files,
        }


def get_typesetting_files(article, previous_round=None):
    """
    Gets queryset of files that may be needed during typesetting.
    File objects will be pre-checked for the user as a convenience
    if they are galleys or if they are proofing files from
    the previous round.
    :param article: an Article object
    :param previous_round: TypesettingRound
    """
    query = Q(manuscript_files=article)
    query |= Q(data_figure_files=article)
    query |= Q(copyeditor_files__article=article)
    query |= Q(galley__article=article)
    query |= Q(supplementaryfile__supp=article)
    query |= Q(galleyproofing__round__article=article)
    queryset = core_models.File.objects

    # Pre-check files that are likely to be needed
    checked_query = Q()
    checked_query |= Q(galley__article=article)
    checked_query |= Q(data_figure_files=article)
    if previous_round:
        checked_query |= Q(
            galleyproofing__round__article=article,
            galleyproofing__round=previous_round,
            galleyproofing__completed__isnull=False,
        )

    queryset = queryset.annotate(
        checked=ExpressionWrapper(
            checked_query,
            output_field=BooleanField()
        )
    )
    return queryset.filter(query).order_by('-last_modified')


def get_typesetters(journal):
    typesetter_pks = [
        role.user.pk for role in core_models.AccountRole.objects.filter(
            role__slug='typesetter',
            journal=journal,
        )
    ]

    return core_models.Account.objects.filter(pk__in=typesetter_pks)


def get_proofreaders(article, round, assignment=None):
    pks = list()
    current_proofer_pks = [
        p.proofreader.pk for p in round.galleyproofing_set.all()
    ]

    for editor in article.editor_list():
        pks.append(editor.pk)

    for author in article.authors.all():
        pks.append(author.pk)

    for proofreader in core_models.AccountRole.objects.filter(
        role__slug='proofreader',
        journal=article.journal
    ):
        pks.append(proofreader.user.pk)

    # If fetching for an assignment we want that user to remain in the list
    if assignment and assignment.proofreader.pk in pks:
        current_proofer_pks.remove(assignment.proofreader.pk)

    return core_models.Account.objects.filter(
        pk__in=pks,
    ).exclude(
        pk__in=current_proofer_pks,
    )


def get_typesetter_notification(assignment, article, request):
    url = request.journal.site_url(reverse("typesetting_assignments"))
    context = {
        'article': article,
        'assignment': assignment,
        'typesetting_assignments_url': url,
    }
    return render_template.get_message_content(
        request,
        context,
        'typesetting_notify_typesetter',
    )


def get_proofreader_notification(assignment, article, request):
    url = request.journal.site_url(
        reverse("typesetting_proofreading_assignments"))
    context = {
        'article': article,
        'assignment': assignment,
        'typesetting_assignments_url': url,
    }
    return render_template.get_message_content(
        request,
        context,
        'typesetting_notify_proofreader',
    )


def handle_proofreader_file(request, assignment, article):
    uploaded_files = request.FILES.getlist('file')

    if uploaded_files:
        for file in uploaded_files:
            new_file = files.save_file_to_article(
                file,
                article,
                request.user,
            )
            new_file.label = 'Proofing File'
            new_file.save()
            assignment.annotated_files.add(new_file)
            messages.add_message(
                request,
                messages.SUCCESS,
                'Annotated file uploaded. '
                'When you are done use the "Mark Task as Complete" button to finish proofreading.',
            )


def new_typesetting_round(article, rounds, request):
    if not rounds:
        new_round = models.TypesettingRound.objects.create(
            article=article,
        )
    else:
        latest_round = rounds[0]
        latest_round.close(request.user)

        if hasattr(latest_round, 'typesettingassignment'):
            notify.event_typesetting_cancelled(
                latest_round.typesettingassignment,
                request,
            )

        new_round = models.TypesettingRound.objects.create(
            article=article,
            round_number=latest_round.round_number + 1,
        )

    return new_round


MISSING_GALLEYS = _("Article has no typeset files")
MISSING_IMAGES = _("One or more typeset files are missing images")
OPEN_TASKS = _(
    "One or more typesetting or proofing tasks haven't been completed"
)


def typesetting_pending_tasks(round):
    pending_tasks = []
    galleys = round.article.galley_set.all()
    if not galleys:
        pending_tasks.append(MISSING_GALLEYS)
    else:
        for galley in galleys:
            if galley.has_missing_image_files():
                pending_tasks.append(MISSING_IMAGES)
                break

    if round.has_open_tasks:
        pending_tasks.append(OPEN_TASKS)

    return pending_tasks


@transaction.atomic
def complete_typesetting(request, article):
    kwargs = {
        'request': request,
        'article': article,
    }

    event_logic.Events.raise_event(
        event_logic.Events.ON_TYPESETTING_COMPLETE,
        task_object=article, **kwargs
    )
    if request.journal.element_in_workflow(element_name='typesetting'):
        workflow_kwargs = {
            'handshake_url': 'typesetting_articles',
            'request': request,
            'article': article,
            'switch_stage': True,
        }

        return event_logic.Events.raise_event(
            event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE,
            task_object=article,
            **workflow_kwargs)
    else:
        messages.add_message(
            request,
            messages.WARNING,
            'There was an error moving this article to the next stage.'
        )
        return redirect(
            reverse('core_dashboard')
        )


def get_next_element(handshake_url, request):
    workflow = core_models.Workflow.objects.get(journal=request.journal)
    workflow_elements = workflow.elements.all()

    current_element = workflow.elements.get(handshake_url=handshake_url)

    try:
        index = list(workflow_elements).index(current_element) + 1
        return workflow_elements[index]
    except IndexError:
        # An index error will occur here when the workflow is complete
        return None


def mint_supp_file_doi(supp_file, doi=None):
    article = supp_file.file.article
    article_doi = article.get_doi()
    if not article_doi:
        raise RuntimeError(
            "Can't issue doi for supp file %s: Article %s has no doi"
            "" % (supp_file.pk, article.pk)
        )

    if not doi and supp_file.doi:
        doi = supp_file.doi
    elif not doi:
        doi = "%s.s%s" % (article_doi, supp_file.pk)

    xml_context = {
        'supp_file': supp_file,
        'article': article,
        'batch_id': uuid.uuid4(),
        'timestamp': int(time.time()),
        'depositor_name': setting_handler.get_setting(
            'Identifiers', 'crossref_name', article.journal,
        ).processed_value,
        'depositor_email': setting_handler.get_setting(
            'Identifiers', 'crossref_email', article.journal,
        ).processed_value,
        'registrant': setting_handler.get_setting(
            'Identifiers', 'crossref_registrant', article.journal,
        ).processed_value,
        'timestamp_suffix': setting_handler.get_setting(
            'crossref', 'crossref_date_suffix', article.journal,
        ).processed_value,
        'parent_doi': article_doi,
        'doi': doi,
        'now': datetime.datetime.now(),
    }
    xml_content = render_to_string(
        'typesetting/crossref/crossref_component.xml',
        xml_context,
    )
    ident_logic.register_crossref_component(article, xml_content, supp_file)

    supp_file.doi = doi
    supp_file.save()

    return doi


def validate_supp_file_doi(supp_file, doi):
    journal = supp_file.file.article.journal
    try:
        submitted_prefix = doi.split("/")[0]
    except (TypeError, ValueError):
        raise ValidationError("'%s' is not a valid DOI" % doi)

    if not DOI_RE.match(doi):
        raise ValidationError("'%s' is not a valid DOI" % doi)

    prefix = setting_handler.get_setting(
        'Identifiers', 'crossref_prefix', journal,
    ).processed_value
    if prefix != submitted_prefix:
        raise ValidationError(
            "'%s' doesn't match the configured prefix '%s'" % (doi, prefix)
        )

    return True

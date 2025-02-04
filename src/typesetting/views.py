from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import Http404
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from typesetting import models, logic, forms, security
from typesetting.notifications import notify
from security import decorators
from submission import models as submission_models
from core import models as core_models, forms as core_forms, files
from production import logic as production_logic
from journal.views import article_figure
from journal import logic as journal_logic
from utils.logger import get_logger

logger = get_logger(__name__)


@decorators.has_journal
@decorators.editor_user_required
def typesetting_manager(request):
    template = 'typesetting/index.html'
    context = {}
    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
def typesetting_articles(request):
    """
    Displays a list of articles in the Typesetting stage.
    :param request: HttpRequest
    :return: HttpResponse
    """
    article_filter = request.GET.get('filter', None)

    articles_in_typesetting = submission_models.Article.objects.filter(
        journal=request.journal,
        stage=submission_models.STAGE_TYPESETTING_PLUGIN,
    )

    if article_filter and article_filter == 'me':
        articles_in_typesetting = articles_in_typesetting.filter(
            typesettingclaim__editor=request.user,
        )

    template = 'typesetting/typesetting_articles.html'
    context = {
        'articles_in_typesetting': articles_in_typesetting,
        'filter': article_filter,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
def typesetting_article(request, article_id):
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    rounds = models.TypesettingRound.objects.filter(article=article)
    galleys = core_models.Galley.objects.filter(
        article=article,
    )
    files = logic.get_typesetting_files(article)
    supp_choice_form = forms.SupplementaryFileChoiceForm(article=article)
    galley_form = forms.GalleyForm()

    if not rounds:
        logic.new_typesetting_round(article, rounds, request.user)
        messages.add_message(
            request,
            messages.INFO,
            'New typesetting round created.',
        )

        return redirect(
            reverse(
                'typesetting_article',
                kwargs={'article_id': article.pk},
            )
        )
    if request.POST and "new-round" in request.POST:
        logic.new_typesetting_round(article, rounds, request)
        messages.add_message(
            request,
            messages.INFO,
            'New typesetting round created.',
        )

        return redirect(
            reverse(
                'typesetting_article',
                kwargs={'article_id': article.pk},
            )
        )

    elif request.POST and "complete-typesetting" in request.POST:
        return logic.complete_typesetting(request, article)

    elif request.POST and 'source' in request.POST:
        for uploaded_file in request.FILES.getlist('source-file'):
            production_logic.save_source_file(
                article,
                request,
                uploaded_file,
            )
            messages.add_message(
                request,
                messages.INFO,
                'Source files uploaded',
            )
    elif request.POST and 'supp' in request.POST:
        for uploaded_file in request.FILES.getlist('supp-file'):
            label = request.POST.get('label', 'Supplementary File')
            production_logic.save_supp_file(
                article, request, uploaded_file, label)
            messages.add_message(
                request,
                messages.INFO,
                'Supplementary file uploaded: %s' % label,
            )

    elif request.POST and 'choice-supp' in request.POST:
        form = forms.SupplementaryFileChoiceForm(request.POST, article=article)
        if form.is_valid():
            supp = form.save()
            messages.add_message(
                request,
                messages.INFO,
                'Supplementary file created',
            )
        return redirect(
            reverse(
                'typesetting_article',
                kwargs={'article_id': article.pk},
            )
        )
    elif request.POST and 'edit-label' in request.POST:
        label = request.POST.get('edit-label', 'Supplementary File')
        supp_file = get_object_or_404(
            core_models.SupplementaryFile,
            id=int(request.POST.get("supp-id", 0)),
        )
        file_obj = supp_file.file
        # Cope with file not having foreign key to article
        if file_obj.article != article:
            raise Http404()
        file_obj.label = label
        file_obj.save()

        messages.add_message(
            request,
            messages.INFO,
            'Label updated: %s' % label,
        )

    template = 'typesetting/typesetting_article.html'
    context = {
        'article': article,
        'rounds': rounds,
        'galleys': galleys,
        'files': files,
        'pending_tasks': logic.typesetting_pending_tasks(rounds[0]),
        'next_element': logic.get_next_element('typesetting_articles', request),
        'supp_choice_form': supp_choice_form,
        'galley_form': galley_form,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
def typesetting_claim_article(request, article_id, action):
    """
    Allows a PM or Editor to claim or unclaim an article.
    :param request: HttpRequest
    :param article_id: int, Article object PK
    :param action: string, either claim or release
    :return: HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    if not hasattr(article, 'typesettingclaim'):

        models.TypesettingClaim.objects.get_or_create(
            editor=request.user,
            article=article,
        )

        messages.add_message(
            request,
            messages.SUCCESS,
            'Article claim successful.'
        )

    elif action == 'unclaim' and article.typesettingclaim.editor == request.user:
        article.typesettingclaim.delete()
        messages.add_message(
            request,
            messages.SUCCESS,
            'Article successfully released.',
        )

    else:
        messages.add_message(
            request,
            messages.ERROR,
            'This article is already being managed by {}.'.format(
                article.typesettingclaim.editor.full_name(),
            )
        )

    return redirect(
        reverse(
            'typesetting_article',
            kwargs={'article_id': article.pk},
        )
    )


@require_POST
@decorators.has_journal
@decorators.typesetting_user_or_production_user_or_editor_required
def typesetting_upload_galley(request, article_id, assignment_id=None):
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    form = forms.GalleyForm(request.POST, request.FILES)
    assignment = None
    galley = None

    if assignment_id:
        assignment = get_object_or_404(
            models.TypesettingAssignment,
            pk=assignment_id,
            typesetter=request.user,
        )

    try:
        if 'file' in request.FILES and form.is_valid():
            label = form.cleaned_data.get('label')
            public = form.cleaned_data.get('public')
            for uploaded_file in request.FILES.getlist('file'):
                galley = production_logic.save_galley(
                    article,
                    request,
                    uploaded_file,
                    True,
                    label=label,
                    public=public,
                )
    except TypeError as exc:
        messages.add_message(request, messages.ERROR, str(exc))
    except UnicodeDecodeError:
        messages.add_message(request, messages.ERROR,
                             "Uploaded file is not UTF-8 encoded")
    except production_logic.ZippedGalleyError:
        messages.add_message(
            request, messages.ERROR,
            "You tried to upload a compressed file. "
            "Please upload each Typeset File separately",
        )

    if assignment and galley:
        assignment.galleys_created.add(galley)

    if not galley:
        messages.add_message(
            request,
            messages.WARNING,
            'No typeset file uploaded',
        )

    if not form.is_valid():
        messages.add_message(
            request,
            messages.WARNING,
            'Galley form not valid.',
        )

    if assignment:
        return redirect(
            reverse(
                'typesetting_assignment',
                kwargs={'assignment_id': assignment.pk}
            )
        )

    return redirect(
        reverse(
            'typesetting_article',
            kwargs={'article_id': article.pk},
        )
    )


@decorators.has_journal
@decorators.typesetting_user_or_production_user_or_editor_required
def typesetting_edit_galley(request, galley_id, article_id):
    """
    Allows a typesetter or editor to edit a Galley file.
    :param request: HttpRequest object
    :param galley_id: Galley object PK
    :param article_id: Article PK, optional
    :return: HttpRedirect or HttpResponse
    """
    return_url = request.GET.get('return', None)

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    galley = get_object_or_404(
        core_models.Galley,
        pk=galley_id,
        article=article,
    )
    galley_form = forms.GalleyForm(
        instance=galley,
        include_file=False,
    )
    if galley.label == 'XML':
        xsl_files = core_models.XSLFile.objects.all()
    else:
        xsl_files = None

    if request.POST:

        if 'delete' in request.POST:

            production_logic.handle_delete_request(
                request,
                galley,
                article=article,
                page="pm_edit",
            )
            if not return_url:
                return redirect(
                    reverse(
                        'typesetting_article',
                        kwargs={'article_id': article.pk},
                    )
                )
            else:
                return redirect(return_url)

        label = request.POST.get('label')

        if 'fixed-image-upload' in request.POST:
            if request.POST.get('datafile') is not None:
                production_logic.use_data_file_as_galley_image(
                    galley,
                    request,
                    label,
                )
            for uploaded_file in request.FILES.getlist('image'):
                production_logic.save_galley_image(
                    galley,
                    request,
                    uploaded_file,
                    label,
                    fixed=True,
                    check_for_existing_images=True,
                )

        if 'image-upload' in request.POST:
            for uploaded_file in request.FILES.getlist('image'):
                production_logic.save_galley_image(
                    galley,
                    request,
                    uploaded_file,
                    label,
                    fixed=False,
                    check_for_existing_images=True,
                )

        elif 'css-upload' in request.POST:
            for uploaded_file in request.FILES.getlist('css'):
                production_logic.save_galley_css(
                    galley,
                    request,
                    uploaded_file,
                    'galley-{0}.css'.format(galley.id),
                    label,
                )

        if 'galley-update' in request.POST:
            galley_form = forms.GalleyForm(
                request.POST,
                instance=galley,
                include_file=False,
            )
            if galley_form.is_valid():
                galley_form.save()

        if 'replace-galley' in request.POST:
            production_logic.replace_galley_file(
                article, request,
                galley,
                request.FILES.get('galley'),
            )

        if 'xsl_file' in request.POST:
            xsl_file = get_object_or_404(core_models.XSLFile,
                                         pk=request.POST["xsl_file"])
            galley.xsl_file = xsl_file
            galley.save()

        return_path = '?return={return_url}'.format(
            return_url=return_url,
        ) if return_url else ''
        url = reverse(
            'typesetting_edit_galley',
            kwargs={'article_id': article.pk, 'galley_id': galley_id},
        )
        redirect_url = '{url}{return_path}'.format(
            url=url,
            return_path=return_path,
        )
        return redirect(redirect_url)

    template = 'typesetting/edit_galley.html'
    context = {
        'galley': galley,
        'article': galley.article,
        'image_names': production_logic.get_image_names(galley),
        'return_url': return_url,
        'data_files': article.data_figure_files.all(),
        'galley_images': galley.images.all(),
        'xsl_files': xsl_files,
        'galley_form': galley_form,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
def typesetting_assign_typesetter(request, article_id):
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    typesetters = logic.get_typesetters(request.journal)
    rounds = models.TypesettingRound.objects.filter(article=article)
    current_round = rounds[0]
    if rounds.count() > 1:
        previous_round = rounds[1]
        proofing_assignments = previous_round.galleyproofing_set.filter(
            completed__isnull=False,
            cancelled=False,
        )
    else:
        previous_round = None
        proofing_assignments = ()

    files = logic.get_typesetting_files(
        article,
        previous_round=previous_round,
    )
    galleys = article.galley_set.all()
    initial_galleys_to_correct = [galley.pk for galley in galleys]
    form = forms.TypesettingAssignmentForm(
        typesetters=typesetters,
        files=files,
        rounds=rounds,
        galleys=galleys,
        initial_galleys_to_correct=initial_galleys_to_correct,
    )

    if request.POST:
        form = forms.TypesettingAssignmentForm(
            request.POST,
            typesetters=typesetters,
            files=files,
            rounds=rounds,
            galleys=galleys,
        )

        if form.is_valid() and form.is_confirmed():
            assignment = form.save()
            assignment.manager = request.user
            assignment.save()

            messages.add_message(
                request,
                messages.SUCCESS,
                'Assignment created.'
            )

            return redirect(
                reverse(
                    'typesetting_notify_typesetter',
                    kwargs={
                        'article_id': article.pk,
                        'assignment_id': assignment.pk
                    }
                )
            )

    template = 'typesetting/assign_typesetter.html'
    context = {
        'article': article,
        'typesetters': typesetters,
        'files': files,
        'galleys': galleys,
        'form': form,
        'round': current_round,
        'proofing_assignments': proofing_assignments,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
@security.require_not_notified(models.TypesettingAssignment)
def typesetting_notify_typesetter(request, article_id, assignment_id):
    """
    Allows the Editor to send a notification email to the typesetter.
    :param request: HttpRequest
    :param article_id: Article object PK
    :param assignment_id: TypesettingAssignment PK
    :return: HttpResponse
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    assignment = get_object_or_404(
        models.TypesettingAssignment,
        pk=assignment_id,
    )

    if assignment.notified:
        messages.add_message(
            request,
            messages.WARNING,
            'A notification has already been sent for this assignment.'
        )

        return redirect(
            reverse(
                'typesetting_article',
                kwargs={'article_id': article.pk},
            )
        )

    if request.POST:
        message = request.POST.get('message')
        notify.event_typesetting_assignment(
            request,
            assignment,
            message,
            skip=True if 'skip' in request.POST else False,
        )
        messages.add_message(
            request,
            messages.SUCCESS,
            'Assignment created.',
        )

        return redirect(
            reverse(
                'typesetting_article',
                kwargs={'article_id': article.pk}
            )
        )

    message = logic.get_typesetter_notification(
        assignment,
        article,
        request,
    )

    template = 'typesetting/notify_typesetter.html'
    context = {
        'article': article,
        'assignment': assignment,
        'message': message,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
def typesetting_review_assignment(request, article_id, assignment_id):
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    assignment = get_object_or_404(
        models.TypesettingAssignment,
        pk=assignment_id,
        round__article=article,
    )
    typesetters = logic.get_typesetters(request.journal)
    files = logic.get_typesetting_files(article)
    galleys = core_models.Galley.objects.filter(
        article=assignment.round.article,
    )
    rounds = models.TypesettingRound.objects.filter(article=article)
    current_round = rounds[0]
    initial_galleys_to_correct = [
        correction.galley.pk for correction in assignment.corrections.all()
    ]
    edit_form = forms.EditTypesettingAssignmentForm(
        typesetters=typesetters,
        files=files,
        galleys=galleys,
        rounds=rounds,
        initial_galleys_to_correct=initial_galleys_to_correct,
        instance=assignment,
    )
    galley_form = forms.GalleyForm()

    decision_form = forms.ManagerDecision()

    if request.POST and (
        edit_form.CONFIRMABLE_BUTTON_NAME in request.POST
        or edit_form.CONFIRMED_BUTTON_NAME in request.POST
    ):
        edit_form = forms.EditTypesettingAssignmentForm(
            request.POST,
            typesetters=typesetters,
            files=files,
            galleys=galleys,
            rounds=rounds,
            instance=assignment,
        )

        if edit_form.is_valid() and edit_form.is_confirmed():
            assignment = edit_form.save()

            assignment.manager = request.user
            assignment.save()

            messages.add_message(
                request,
                messages.SUCCESS,
                'Assignment updated.'
            )
    elif request.POST and "delete" in request.POST:
        assignment.delete(request.user)
        notify.event_typesetting_deleted(
            assignment,
            request,
        )
        return redirect(
            reverse(
                'typesetting_article',
                kwargs={'article_id': article.pk},
            )
        )
    elif request.POST and "reopen" in request.POST:
        assignment.reopen(request.user)
        return redirect(
            reverse(
                'typesetting_notify_typesetter',
                kwargs={
                    'article_id': article.pk,
                    'assignment_id': assignment.pk
                }
            )
        )

    elif request.POST and "decision" in request.POST:
        decision_form = forms.ManagerDecision(
            request.POST,
            instance=assignment,
        )

        if decision_form.is_valid():
            decision_form.save()
            return redirect(
                reverse(
                    'typesetting_article',
                    kwargs={'article_id': article.pk},
                )
            )

    template = 'typesetting/typesetting_review_assignment.html'
    context = {
        'article': article,
        'assignment': assignment,
        'galleys': galleys,
        'form': edit_form,
        'typesetters': typesetters,
        'files': files,
        'galley_form': galley_form,
        'proofing_assignments': assignment.proofing_assignments_for_corrections,
        'decision_form': decision_form,
        'pending_corrections': [
            correction for correction in assignment.corrections.all()
            if not correction.corrected
        ],
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.typesetter_user_required
def typesetting_assignments(request):

    assignments = models.TypesettingAssignment.active_objects.filter(
        typesetter=request.user,
        round__article__journal=request.journal,
    )

    active_assignments = assignments.filter(
        completed__isnull=True,
        cancelled__isnull=True,
    )

    past_assignments = assignments.filter(
        Q(completed__isnull=False) | Q(cancelled__isnull=False),
    )

    template = 'typesetting/typesetting_assignments.html'
    context = {
        'active_assignments': active_assignments,
        'past_assignments': past_assignments,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.typesetter_user_required
def typesetting_typesetter_download_file(request, assignment_id, file_id):
    assignment = get_object_or_404(
        models.TypesettingAssignment,
        pk=assignment_id,
        typesetter=request.user,
        completed__isnull=True,
        round__article__journal=request.journal,
    )

    file = get_object_or_404(
        core_models.File,
        pk=file_id,
        article_id=assignment.round.article.pk,
    )

    if (
        file in assignment.files_to_typeset.all()
        or file in assignment.round.article.data_figure_files.all()
        or assignment.proofing_assignments_for_corrections().filter(
            annotated_files__id=file_id)
        or file.pk in assignment.round.article.supplementary_files.values_list(
            'file__pk', flat=True,
            )
        or file.pk in assignment.round.article.galley_set.values_list(
                'file__pk', flat=True,
            )
    ):
        return files.serve_any_file(
            request,
            file,
            path_parts=('articles', assignment.round.article.pk),
        )
    else:
        raise PermissionDenied(
            'You do not have permission to view this file.',
        )


@decorators.has_journal
@security.user_can_manage_file
def typesetting_download_file(request, article_id, file_id):
    """
    A view that serves up a file for a given article.
    """
    file = get_object_or_404(
        core_models.File,
        pk=file_id,
        article_id=article_id,
    )

    return files.serve_any_file(
        request,
        file,
        path_parts=('articles', article_id)
    )


@decorators.has_journal
@decorators.production_user_or_editor_required
def typesetting_delete_galley(request, galley_id):
    """
    Allows users with permission to delete files
    """
    galley = get_object_or_404(
        core_models.Galley,
        pk=galley_id,
        article__journal=request.journal,
    )

    # Grab the article and delete the Galley but retain the file.
    article = galley.article
    galley.delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        'Galley deleted.',
    )

    return redirect(
        reverse(
            'typesetting_article',
            kwargs = {'article_id': article.pk},
        )
    )


@decorators.has_journal
@decorators.typesetter_user_required
def typesetting_assignment(request, assignment_id):
    assignment = get_object_or_404(
        models.TypesettingAssignment.active_objects,
        pk=assignment_id,
        typesetter=request.user,
        completed__isnull=True,
        round__article__journal=request.journal
    )
    article = assignment.round.article

    # Display galleys that were selected by the editor
    # or that were uploaded by the typesetter
    galleys = core_models.Galley.objects.filter(
        Q(article=article),
        (Q(file__files_to_typeset=assignment) | Q(file__owner=request.user)),
    ).distinct()

    supplementary_files = article.supplementary_files.filter(
        file__pk__in=[file.pk for file in assignment.files_to_typeset.all()],
    )

    form = forms.TypesetterDecision()
    galley_form = forms.GalleyForm()
    complete_form = core_forms.SimpleTinyMCEForm(field_name='note_from_typesetter')
    complete_form.fields['note_from_typesetter'].required = False

    if request.POST:
        if 'source' in request.POST:
            for uploaded_file in request.FILES.getlist('source-file'):
                production_logic.save_source_file(
                    article,
                    request,
                    uploaded_file,
                )
                messages.add_message(
                    request,
                    messages.INFO,
                    'Source files uploaded',
                )

        if assignment.cancelled:
            messages.add_message(
                request,
                messages.WARNING,
                'The manager for this article has cancelled this typesetting'
                'task. No further changes are allowed',
            )
            return redirect(reverse(
                'typesetting_assignment',
                kwargs={'assignment_id': assignment.pk},
            ))

        if 'complete_typesetting' in request.POST:
            note = request.POST.get('note_from_typesetter', None)
            assignment.complete(note, request.user)
            notify.event_complete_notification(assignment, request)

            return redirect(reverse('typesetting_assignments'))

        form = forms.TypesetterDecision(request.POST)

        if form.is_valid():
            note = form.cleaned_data.get('note', 'No note supplied.')
            decision = form.cleaned_data.get('decision')
            if decision == 'accept':
                assignment.accepted = timezone.now()
                assignment.save()
                notify.event_decision_notification(
                    assignment,
                    request,
                    note,
                    decision,
                )
                return redirect(reverse(
                    'typesetting_assignment',
                    kwargs={'assignment_id': assignment.pk},
                ))
            else:
                assignment.completed = timezone.now()
                for correction in assignment.corrections.all():
                    if correction.corrected and not correction.date_completed:
                        correction.date_completed = timezone.now()
                assignment.save()
                notify.event_decision_notification(
                    assignment,
                    request,
                    note,
                    decision,
                )
                messages.add_message(
                    request,
                    messages.INFO,
                    'Thanks, the manager has been informed.'
                )

                return redirect(reverse('typesetting_assignments'))

    template = 'typesetting/typesetting_assignment.html'
    context = {
        'assignment': assignment,
        'article': assignment.round.article,
        'form': form,
        'galleys': galleys,
        'pending_corrections': [
            correction for correction in assignment.corrections.all()
            if not correction.corrected
        ],
        'missing_images': [g for g in galleys if g.has_missing_image_files()],
        'supplementary_files': supplementary_files,
        'proofing_assignments': assignment.proofing_assignments_for_corrections,
        'galley_form': galley_form,
        'complete_form': complete_form,
    }

    return render(request, template, context)


@decorators.production_user_or_editor_required
def typesetting_delete_correction(request, correction_id):
    try:
        correction = models.TypesettingCorrection.objects.get(
            task__round__article__journal=request.journal,
            pk=correction_id,
        )
    except models.TypesettingCorrection.DoesNotExist:
        messages.add_message(
            request,
            messages.WARNING,
            'Correction already adressed',
        )

    else:
        correction.delete()
        if correction.galley:
            messages.add_message(
                request,
                messages.INFO,
                'Correction Deleted',
            )
        else:
            messages.add_message(
                request,
                messages.INFO,
                'Confirmed',
            )
    return redirect(request.META.get('HTTP_REFERER'))


@decorators.has_journal
@decorators.production_user_or_editor_required
def typesetting_assign_proofreader(request, article_id):
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    rounds = models.TypesettingRound.objects.filter(article=article)
    proofreaders = logic.get_proofreaders(article, rounds[0])
    galleys = core_models.Galley.objects.filter(
        article=article,
    )

    if not galleys:
        messages.add_message(
            request,
            messages.WARNING,
            'You cannot assign a proofreader without typeset files.',
        )

        return redirect(reverse(
            'typesetting_article',
            kwargs={'article_id': article.pk},
        ))

    form = forms.AssignProofreader(
        proofreaders=proofreaders,
        round=rounds[0],
        user=request.user,
    )

    if request.POST:
        form = forms.AssignProofreader(
            request.POST,
            proofreaders=proofreaders,
            round=rounds[0],
            user=request.user,
        )

        if form.is_valid() and form.is_confirmed():
            assignment = form.save()

            messages.add_message(
                request,
                messages.SUCCESS,
                'Proofing Assignment created.'
            )

            return redirect(
                reverse(
                    'typesetting_notify_proofreader',
                    kwargs={
                        'article_id': article.pk,
                        'assignment_id': assignment.pk,
                    }
                )
            )

    template = 'typesetting/typesetting_assign_proofreader.html'
    context = {
        'article': article,
        'proofreaders': proofreaders,
        'form': form,
        'galleys': galleys,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
@security.require_not_notified(models.GalleyProofing)
def typesetting_notify_proofreader(request, article_id, assignment_id):
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    assignment = get_object_or_404(
        models.GalleyProofing,
        pk=assignment_id,
        completed__isnull=True,
        notified=False,
    )
    message = logic.get_proofreader_notification(
        assignment,
        article,
        request,
    )

    if request.POST:
        message = request.POST.get('message')
        skip = True if 'skip' in request.POST else False
        assignment.assign(
            user=request.user,
            skip=skip
        )
        notify.galley_proofing_assignment(
            request,
            assignment,
            message,
            skip=skip
        )
        messages.add_message(
            request,
            messages.SUCCESS,
            'Assignment created',
        )

        return redirect(
            reverse(
                'typesetting_article',
                kwargs={'article_id': article.pk},
            )
        )

    template = 'typesetting/typesetting_notify_proofreader.html'
    context = {
        'article': article,
        'assignment': assignment,
        'message': message,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
def typesetting_manage_proofing_assignment(request, article_id, assignment_id):
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    assignment = get_object_or_404(
        models.GalleyProofing,
        pk=assignment_id,
    )
    proofreaders = logic.get_proofreaders(
        article,
        assignment.round,
        assignment=assignment,
    )

    form = forms.EditProofingAssignment(
        instance=assignment,
    )

    if request.POST:

        if 'action' in request.POST:

            action = request.POST.get('action')

            if action == 'cancel':
                assignment.cancel(
                    user=request.user
                )
                notify.galley_proofing_cancel(
                    request,
                    assignment,
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Proofing task cancelled.',
                )
            elif action == 'reset':
                assignment.reset(
                    user=request.user
                )
                notify.galley_proofing_reset(
                    request,
                    assignment,
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Proofing task reset.',
                )
            elif action == 'complete':
                assignment.complete(
                    user=request.user,
                )
                notify.galley_proofing_complete(
                    request,
                    assignment,
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Proofing task completed.',
                )

            return redirect(
                reverse(
                    'typesetting_article',
                    kwargs={'article_id': article.pk},
                )
            )

        form = forms.EditProofingAssignment(
            request.POST,
            instance=assignment,
        )

        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Assignment updated.',
            )

            return redirect(
                reverse(
                    'typesetting_manage_proofing_assignment',
                    kwargs={
                        'article_id': article.pk,
                        'assignment_id': assignment.pk,
                    }
                )
            )

    template = 'typesetting/typesetting_manage_proofing_assignment.html'
    context = {
        'article': article,
        'assignment': assignment,
        'proofreaders': proofreaders,
        'form': form,
    }

    return render(request, template, context)


@login_required
def typesetting_proofreading_assignments(request):
    assignments = models.GalleyProofing.active_objects.filter(
        proofreader=request.user,
        round__article__journal=request.journal,
    )

    active_assignments = assignments.filter(
        completed__isnull=True,
    )

    completed_assignments = assignments.filter(
        completed__isnull=False,
    )

    template = 'typesetting/typesetting_proofing_assignments.html'
    context = {
        'active_assignments': active_assignments,
        'completed_assignments': completed_assignments,
    }

    return render(request, template, context)


@security.proofreader_for_article_required
def typesetting_proofreading_assignment(request, assignment_id):
    assignment = get_object_or_404(
        models.GalleyProofing.active_objects,
        pk=assignment_id,
        completed__isnull=True,
        cancelled=False,
    )
    galleys = core_models.Galley.objects.filter(
        article=assignment.round.article,
    )

    form = forms.ProofingForm(instance=assignment)

    if request.POST:
        form = forms.ProofingForm(request.POST, instance=assignment)

        if request.FILES:
            logic.handle_proofreader_file(
                request,
                assignment,
                assignment.round.article,
            )

        if form.is_valid():
            form.save()

            if form.is_confirmed():
                assignment.complete(
                    user=request.user
                )
                notify.galley_proofing_complete(
                    request,
                    assignment
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Proofreading Assignment complete.',
                )
                return redirect(
                    reverse(
                        'core_dashboard',
                    )
                )

    template = 'typesetting/typesetting_proofreading_assignment.html'
    context = {
        'assignment': assignment,
        'galleys': galleys,
        'form': form,
    }

    return render(request, template, context)


@security.can_preview_typesetting_article
def typesetting_preview_galley(
        request,
        article_id,
        galley_id,
        assignment_id=None,
):
    """
    Displays a preview of a galley object
    :param request: HttpRequest object
    :param assignment_id: ProofingTask object PK
    :param galley_id: Galley object PK
    :param article_id: Article object PK
    :param assignment_id: Optional proofing or typesetting assignment id
    :return: HttpResponse
    """
    proofing_task = None
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    galley = get_object_or_404(
        core_models.Galley,
        pk=galley_id,
        article_id=article.pk,
    )

    if assignment_id:
        try:
            proofing_task = models.GalleyProofing.objects.get(
                pk=assignment_id,
                round__article=article,
            )
            proofing_task.proofed_files.add(galley)
        except models.GalleyProofing.DoesNotExist:
            get_object_or_404(
                models.TypesettingAssignment,
                pk=assignment_id,
            )

    if galley.type == 'xml' or galley.type == 'html':
        template = 'journal/article.html'
    elif galley.type == 'epub':
        template = 'proofing/preview/epub.html'
    else:
        template = 'typesetting/preview_embedded.html'

    article_content = galley.file_content()
    galleys = article.galley_set.filter(public=True)

    context = {
        'proofing': True,
        'proofing_task': proofing_task,
        'galley': galley,
        'galleys': galleys,
        'article': article if article else proofing_task.round.article,
        'identifier_type': 'id',
        'identifier': article.pk if article else proofing_task.round.article.pk,
        'article_content': article_content,
        'tables_in_galley': journal_logic.get_all_tables_from_html(article_content),
    }

    return render(request, template, context)


@security.proofreader_for_article_required
def typesetting_proofing_download(request, article_id, assignment_id, file_id):
    """
    Serves a galley for proofreader
    """
    assignment = get_object_or_404(
        models.GalleyProofing,
        pk=assignment_id,
        round__article__id=article_id,
    )
    file = get_object_or_404(core_models.File, pk=file_id)
    try:
        galley = core_models.Galley.objects.get(
            article_id=assignment.round.article.pk,
            file=file,
        )
        assignment.proofed_files.add(galley)
        return files.serve_file(request, file, assignment.round.article)
    except core_models.Galley.DoesNotExist:
        messages.add_message(
            request,
            messages.WARNING,
            'Requested file is not a typeset file for proofing',
        )
        return redirect(request.META.get('HTTP_REFERER'))


@security.can_preview_typesetting_article
def preview_figure(
        request,
        galley_id,
        file_name,
        assignment_id=None,
        article_id=None,
):

    if assignment_id:
        try:
            assignment = models.TypesettingAssignment.objects.get(
                pk=assignment_id,
                typesetter=request.user,
            )
            galley = core_models.Galley.objects.get(
                pk=galley_id,
                article_id=assignment.round.article.pk,
            )
        except (models.TypesettingAssignment.DoesNotExist, core_models.Galley.DoesNotExist):
            assignment = get_object_or_404(
                models.GalleyProofing,
                pk=assignment_id,
                proofreader=request.user
            )
            galley = get_object_or_404(
                core_models.Galley,
                pk=galley_id,
                article_id=assignment.round.article.pk,
            )
    elif article_id and request.user.has_an_editor_role(request):
        article = get_object_or_404(
            submission_models.Article,
            pk=article_id,
            journal=request.journal,
        )
        galley = get_object_or_404(
            core_models.Galley,
            pk=galley_id,
            article_id=article.pk,
        )
    else:
        raise PermissionDenied

    return article_figure(request, galley.article.pk, galley.pk, file_name)


@security.user_can_manage_file
def article_file_make_galley(request, article_id, file_id):
    """ Copies a file to be a publicly available galley

    :param request: the request associated with this call
    :param article_id: the ID of the associated articled
    :param file_id: the file ID for which to view the history
    :return: a redirect to the URL at the GET parameter 'return'
    """
    article_object = get_object_or_404(
        submission_models.Article, pk=article_id)
    janeway_file = get_object_or_404(
        core_models.File, pk=file_id)

    blob = janeway_file.get_file(article_object, as_bytes=True)
    content_file = ContentFile(blob)
    content_file.name = janeway_file.original_filename
    production_logic.save_galley(
        article_object, request, content_file,
        is_galley=True,
    )


    return redirect(request.GET['return'])


@require_POST
@decorators.production_user_or_editor_required
def mint_supp_doi(request, supp_file_id):
    supp_file = get_object_or_404(
        core_models.SupplementaryFile,
        id=supp_file_id,
    )
    # Cope with file not having foreign key to article
    if supp_file.file.article.journal != request.journal:
        raise Http404()

    doi = request.POST.get("doi")
    if not doi:
        messages.add_message(
            request,
            messages.ERROR,
            'The DOI field must be filled in',
        )
    else:
        try:
            logic.validate_supp_file_doi(supp_file, doi)
            doi = logic.mint_supp_file_doi(supp_file, doi)
        except ValidationError as e:
            messages.add_message(
                request,
                messages.ERROR,
                'Invalid DOI: %s' % e.message,
            )
        except Exception as e:
            messages.add_message(
                request,
                messages.ERROR,
                'There was a problem minting the DOI,'
                ' the site administrator has been alerted',
            )
            logger.exception("Error minting supplementary file DOI %s", e)
        else:
            messages.add_message(
                request,
                messages.INFO,
                'Minted DOI for supplementary file #%d' % supp_file.pk,
            )

    return redirect(request.META.get('HTTP_REFERER'))

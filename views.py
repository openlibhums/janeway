from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from plugins.typesetting import plugin_settings, models, logic, forms
from security import decorators
from submission import models as submission_models
from core import models as core_models, files
from production import logic as production_logic


@decorators.has_journal
@decorators.editor_user_required
def typesetting_manager(request):
    pass


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
        stage=plugin_settings.STAGE,
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
    manuscript_files = logic.production_ready_files(article)

    if not rounds:
        models.TypesettingRound.objects.create(
            article=article,
        )

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

    template = 'typesetting/typesetting_article.html'
    context = {
        'article': article,
        'rounds': rounds,
        'galleys': galleys,
        'manuscript_files': manuscript_files,
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
        if request.user.is_production(request) or request.user.has_an_editor_role(request):

            models.TypesettingClaim.objects.get_or_create(
                editor=request.user,
                article=article,
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                'Article claim successful.'
            )
        else:
            messages.add_message(
                request,
                messages.WARNING,
                'You must be an Editor or Production Manager.'
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

    try:
        if 'xml' in request.POST:
            for uploaded_file in request.FILES.getlist('xml-file'):
                production_logic.save_galley(
                    article,
                    request,
                    uploaded_file,
                    True,
                )
    except TypeError as exc:
        messages.add_message(request, messages.ERROR, str(exc))
    except UnicodeDecodeError:
        messages.add_message(request, messages.ERROR,
                             "Uploaded file is not UTF-8 encoded")

    if 'pdf' in request.POST:
        for uploaded_file in request.FILES.getlist('pdf-file'):
            production_logic.save_galley(
                article,
                request,
                uploaded_file,
                True,
                "PDF",
            )

    if 'other' in request.POST:
        for uploaded_file in request.FILES.getlist('other-file'):
            production_logic.save_galley(
                article,
                request,
                uploaded_file,
                True,
                "Other",
            )

    if 'prod' in request.POST:
        for uploaded_file in request.FILES.getlist('prod-file'):
            production_logic.save_prod_file(
                article,
                request,
                uploaded_file,
                'Production Ready File',
            )

    if assignment_id:

        assignment = get_object_or_404(
            models.TypesettingAssignment,
            pk=assignment_id,
            typesetter=request.user,
        )

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
                )

        if 'image-upload' in request.POST:
            for uploaded_file in request.FILES.getlist('image'):
                production_logic.save_galley_image(
                    galley,
                    request,
                    uploaded_file,
                    label,
                    fixed=False,
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

        if 'galley-label' in request.POST:
            galley.label = request.POST.get('galley_label')
            galley.save()

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
    files = logic.production_ready_files(article, file_objects=True)
    rounds = models.TypesettingRound.objects.filter(article=article)

    form = forms.AssignTypesetter(
        typesetters=typesetters,
        files=files,
        rounds=rounds,
    )

    if request.POST:
        form = forms.AssignTypesetter(
            request.POST,
            typesetters=typesetters,
            files=files,
            rounds=rounds,
        )

        if form.is_valid():
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
        'files': logic.production_ready_files(article),
        'form': form,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.production_user_or_editor_required
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

        assignment.send_notification(
            message,
            request,
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

    galleys = core_models.Galley.objects.filter(
        article=assignment.round.article,
    )

    template = 'typesetting/typesetting_review_assignment.html'
    context = {
        'article': article,
        'assignment': assignment,
        'galleys': galleys,
    }

    return render(request, template, context)


@decorators.has_journal
@decorators.typesetter_user_required
def typesetting_assignments(request):
    assignments = models.TypesettingAssignment.objects.filter(
        typesetter=request.user,
        round__article__journal=request.journal,
        completed__isnull=True,
    )

    template = 'typesetting/typesetting_assignments.html'
    context = {
        'assignments': assignments,
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

    if file in assignment.files_to_typeset.all():
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
@decorators.typesetter_user_required
def typesetting_assignment(request, assignment_id):
    assignment = get_object_or_404(
        models.TypesettingAssignment,
        pk=assignment_id,
        typesetter=request.user,
        completed__isnull=True,
        round__article__journal=request.journal
    )
    galleys = core_models.Galley.objects.filter(
        article=assignment.round.article,
    )

    form = forms.TypesetterDecision()

    if request.POST:

        if 'complete_typesetting' in request.POST:
            note = request.POST.get('note_from_typesetter', None)
            assignment.complete(note, galleys)
            assignment.send_complete_notification(request)

            return redirect(reverse('typesetting_assignments'))

        form = forms.TypesetterDecision(request.POST)

        if form.is_valid():
            note = form.cleaned_data.get('note', 'No note supplied.')
            decision = form.cleaned_data.get('decision')
            if decision == 'accept':
                assignment.accepted = timezone.now()
                assignment.save()
                assignment.send_decision_notification(request, note, decision)
                return redirect(reverse(
                    'typesetting_assignment',
                    kwargs={'assignment_id': assignment.pk},
                ))
            else:
                assignment.completed = timezone.now()
                assignment.save()
                assignment.send_decision_notification(request, note, decision)
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
    }

    return render(request, template, context)

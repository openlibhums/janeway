__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import datetime
import uuid
from zipfile import BadZipFile

from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from events import logic as event_logic
from core import models as core_models
from cron import models as cron_task
from production import logic, models, forms
from security.decorators import (
    editor_user_required,
    production_user_or_editor_required,
    article_production_user_required,
    article_stage_production_required,
    has_journal,
    typesetter_or_editor_required,
    typesetter_user_required,
    typesetting_user_or_production_user_or_editor_required,
    production_manager_roles
)
from submission import models as submission_models
from utils import setting_handler
from journal.views import article_figure


@production_manager_roles
def production_list(request):
    """
    Diplays a list of new, assigned and the user's production assignments.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    assigned_table = models.ProductionAssignment.objects.filter(
        article__journal=request.journal
    )
    my_table = models.ProductionAssignment.objects.values_list(
        'article_id',
        flat=True
    ).filter(
        production_manager=request.user,
        article__journal=request.journal
    )

    assigned = [assignment.article.pk for assignment in assigned_table]
    unassigned_articles = submission_models.Article.objects.filter(
        stage=submission_models.STAGE_TYPESETTING,
        journal=request.journal
    ).exclude(
        id__in=assigned
    )
    assigned_articles = submission_models.Article.objects.filter(
        stage=submission_models.STAGE_TYPESETTING,
        journal=request.journal
    ).exclude(
        id__in=unassigned_articles
    )

    my_articles = submission_models.Article.objects.filter(
        stage=submission_models.STAGE_TYPESETTING,
        id__in=my_table
    )

    prod_managers = core_models.AccountRole.objects.filter(
        role__slug='production',
        journal=request.journal
    )

    template = 'production/index.html'
    context = {
        'production_articles': unassigned_articles,
        'assigned_articles': assigned_articles,
        'production_managers': prod_managers,
        'my_articles': my_articles,
    }

    return render(request, template, context)


@has_journal
@editor_user_required
@article_stage_production_required
def production_assign_article(request, user_id, article_id):
    """
    Allows an editor to assign a production manager to an article.
    :param request: HttpRequest object
    :param user_id: Account object PK
    :param article_id: Article object PK
    :return: HttpRedirect
    """
    article = submission_models.Article.objects.get(
        id=article_id,
        journal=request.journal,
    )
    user = core_models.Account.objects.get(id=user_id)

    if user.is_production(request):
        url = request.journal.site_url(
            path=reverse(
                'production_article',
                kwargs={'article_id': article.id},
            )
        )
        html = logic.get_production_assign_content(user, request, article, url)

        prod = models.ProductionAssignment(
            article=article,
            production_manager=user,
            editor=request.user,
        )
        prod.save()

        cron_task.CronTask.add_email_task(
            user.email,
            'Production assignment',
            html,
            request,
            article,
        )
    else:
        messages.add_message(
            request,
            messages.WARNING,
            'User is not a production manager.',
        )

    return redirect(reverse('production_list'))


@editor_user_required
@article_stage_production_required
def production_unassign_article(request, article_id):
    """
    Removes a ProductionAssignment by deleting it.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpRedirect
    """
    article = submission_models.Article.objects.get(
        id=article_id,
        journal=request.journal,
    )

    models.ProductionAssignment.objects.filter(article=article).delete()

    return redirect(reverse('production_list'))


@editor_user_required
def non_workflow_assign_article(request, article_id):
    """
    Allows users to assign themselves as production manager outside the
    standard workflow process.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    if article.production_assignment_or_none():
        messages.add_message(
            request,
            messages.WARNING,
            'This article already has a production assignment.',
        )

        return redirect(
            reverse(
                'production_article',
                kwargs={'article_id': article.pk},
            )
        )

    if request.POST and 'assign' in request.POST:
        models.ProductionAssignment.objects.create(
            article=article,
            editor=request.user,
            production_manager=request.user,
            assigned=timezone.now(),
            notified=True,
        )

        messages.add_message(
            request,
            messages.SUCCESS,
            'Production Assignment created.',
        )

        return redirect(
            reverse(
                'production_article',
                kwargs={'article_id': article.pk},
            )
        )

    template = 'production/non_workflow_assign.html'
    context = {
        'article': article,
    }

    return render(request, template, context)


@require_POST
@article_production_user_required
@article_stage_production_required
def production_done(request, article_id):
    """
    Allows a Production Manager to mark Production as complete, fires an event
    that emails the Editor.
    :param request: HttpRequest object
    :param article_id: Artcle object PK
    :return: HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    assignment = models.ProductionAssignment.objects.get(article=article)
    assignment.closed = timezone.now()

    for task in assignment.typesettask_set.all():
        if not task.completed:
            task.completed = timezone.now()
        task.editor_reviewed = True

        task.save()

    assignment.save()

    kwargs = {
        'request': request,
        'article': article,
        'assignment': assignment,
        'user_content_message': request.POST.get('user_content_message'),
        'skip': True if 'skip' in request.POST else False
    }
    event_logic.Events.raise_event(event_logic.Events.ON_PRODUCTION_COMPLETE, **kwargs)

    if request.journal.element_in_workflow(element_name='production'):
        workflow_kwargs = {'handshake_url': 'production_list', 'request': request, 'article': article,
                           'switch_stage': True}
        return event_logic.Events.raise_event(event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE, task_object=article,
                                              **workflow_kwargs)
    else:
        return redirect('proofing_list')


@production_user_or_editor_required
def production_article(request, article_id):
    """
    Displays typesetting tasks, Galleys and allows new Galleys to be uploaded.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpResponse object
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    try:
        production_assignment = models.ProductionAssignment.objects.get(
            article=article
        )
    except models.ProductionAssignment.DoesNotExist:
        return redirect(
           reverse(
               'production_non_workflow_assign',
               kwargs={'article_id': article.pk},
           )
       )

    galleys = logic.get_all_galleys(production_assignment.article)

    if request.POST:
        try:
            if 'file' in request.FILES:
                label = request.POST.get('label', None)
                for uploaded_file in request.FILES.getlist('file'):
                    logic.save_galley(
                        article,
                        request,
                        uploaded_file,
                        True,
                        label=label,
                    )
        except TypeError as exc:
            messages.add_message(request, messages.ERROR, str(exc))
        except UnicodeDecodeError:
            messages.add_message(request, messages.ERROR,
                "Uploaded file is not UTF-8 encoded")
        except logic.ZippedGalleyError:
            messages.add_message(request, messages.ERROR,
                "Galleys must be uploaded individually, not zipped",
            )


        if 'prod' in request.POST:
            for uploaded_file in request.FILES.getlist('prod-file'):
                logic.save_prod_file(
                    article,
                    request,
                    uploaded_file,
                    'Production Ready File',
                )

        if 'supp' in request.POST:
            label = request.POST.get('label', 'Supplementary File')
            for uploaded_file in request.FILES.getlist('supp-file'):
                logic.save_supp_file(article, request, uploaded_file, label)

        if 'source' in request.POST:
            for uploaded_file in request.FILES.getlist('source-file'):
                logic.save_source_file(
                    article,
                    request,
                    uploaded_file,
                )
        if not request.FILES:
            messages.add_message(
                request,
                messages.WARNING,
                'No files uploaded.'
            )

        return redirect(
            reverse(
                'production_article',
                kwargs={'article_id': article.pk}
            )
        )

    manuscripts = article.manuscript_files.filter(is_galley=False)
    data_files = article.data_figure_files.filter(is_galley=False)
    copyedit_files = logic.get_copyedit_files(article)

    template = 'production/assigned_article.html'
    context = {
        'article': article,
        'manuscripts': manuscripts,
        'data_files': data_files,
        'production_assignment': production_assignment,
        'copyedit_files': copyedit_files,
        'typeset_tasks': production_assignment.typesettask_set.all().order_by('-id'),
        'galleys': galleys,
        'complete_message': logic.get_complete_template(request, article, production_assignment)
    }

    return render(request, template, context)


@typesetting_user_or_production_user_or_editor_required
def preview_galley(request, article_id, galley_id):
    """
    Displays a preview of a galley object
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param galley_id: Galley object PK
    :return: HttpResponse
    """
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

    article_content = ""
    if galley.type == 'xml' or galley.type == 'html':
        template = 'proofing/preview/rendered.html'
        try:
            article_content = galley.file_content()
        except Exception as e:
            messages.add_message(
                request,
                messages.ERROR,
                'Errors found rendering this galley',
            )
            article_content  = "Errors found rendering this galley: \n%s" % e
    elif galley.type == 'epub':
        template = 'proofing/preview/epub.html'
    else:
        template = 'proofing/preview/embedded.html'

    context = {
        'galley': galley,
        'article': article,
        'article_content': article_content,
    }

    return render(request, template, context)


@typesetting_user_or_production_user_or_editor_required
def preview_figure(request, article_id, galley_id, file_name):
    galley = get_object_or_404(core_models.Galley,
                               pk=galley_id,
                               article__pk=article_id,
                               article__journal=request.journal)
    return article_figure(request, galley.article.pk, galley_id, file_name)


@article_stage_production_required
@production_user_or_editor_required
def assign_typesetter(request, article_id, production_assignment_id):
    """
    Lets a production manager assign a typesetter a task
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param production_assignment_id: ProductionAssignment object PK
    :return: HttpRedirect if POST otherwise HttpResponse
    """
    production_assignment = get_object_or_404(
        models.ProductionAssignment,
        pk=production_assignment_id,
        article__journal=request.journal,
        closed__isnull=True,
    )
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    copyedit_files = logic.get_copyedit_files(article)
    typesetters = logic.get_typesetters(article)
    typesetter_form = forms.AssignTypesetter(
        article=article,
        files=copyedit_files,
        typesetters=typesetters,
        assignment=production_assignment,
    )

    if request.POST.get('typesetter_id'):
        task = logic.handle_self_typesetter_assignment(
            production_assignment,
            request
        )
        return redirect(
            reverse(
                'do_typeset_task',
                kwargs={'typeset_id': task.id}
            )
        )

    if request.POST:
        typesetter_form = forms.AssignTypesetter(
            request.POST,
            request.FILES,
            article=article,
            files=copyedit_files,
            typesetters=typesetters,
            assignment=production_assignment,
        )

        if typesetter_form.is_valid():
            task = typesetter_form.save()

            return redirect(
                reverse(
                    'notify_typesetter',
                    kwargs={'typeset_id': task.pk}
                )
            )

    template = 'production/assign_typesetter.html'
    context = {
        'production_assignment': production_assignment,
        'article': article,
        'copyedit_files': copyedit_files,
        'typesetters': typesetters,
        'form': typesetter_form,
    }

    return render(request, template, context)


@article_stage_production_required
@production_user_or_editor_required
def notify_typesetter(request, typeset_id, event=True):
    """
    Optionally allows the PM to send the Typesetter an email, it can be skpped.
    :param request: HttpRequest object
    :param typeset_id: TypesetTask object PK
    :param event: string either 'true' or 'false'
    :return: HttpRedirect if POST otherwise HttpResponse
    """
    typeset = get_object_or_404(
        models.TypesetTask,
        pk=typeset_id,
        assignment__article__journal=request.journal,
    )

    if typeset.notified:
        messages.add_message(
            request,
            messages.INFO,
            'A notification has already been sent for this task.',
        )

        return redirect(
            reverse(
                'production_article',
                kwargs={'article_id': typeset.assignment.article.pk},
            )
        )

    user_message_content = logic.get_typesetter_notification(typeset, request)

    if request.POST:
        user_message_content = request.POST.get('user_message_content')
        kwargs = {
            'user_message_content': user_message_content,
            'typeset_task': typeset,
            'request': request,
            'skip': True if 'skip' in request.POST else False,
        }

        if 'skip' not in request.POST:
            typeset.notified = True
            typeset.save()

        if event or event == 'true':
            event_logic.Events.raise_event(
                event_logic.Events.ON_TYPESET_TASK_ASSIGNED, **kwargs)

        return redirect(reverse('production_article', kwargs={
            'article_id': typeset.assignment.article.pk}))

    template = 'production/notify_typesetter.html'
    context = {
        'typeset_task': typeset,
        'user_message_content': user_message_content,
    }

    return render(request, template, context)


@article_stage_production_required
@production_user_or_editor_required
def edit_typesetter_assignment(request, typeset_id):
    """
    Allows the editor to edit an incomplete typesetting assignment.
    :param request: django request object
    :param typeset_id: Typesetting Assignment PK
    :return: HttpRedirect if POST otherwise HttpResponse
    """
    typeset = get_object_or_404(
        models.TypesetTask,
        pk=typeset_id,
        assignment__article__journal=request.journal,
    )
    article = typeset.assignment.article

    if request.POST:
        if 'delete' in request.POST:
            messages.add_message(
                request,
                messages.SUCCESS,
                'Typeset task {0} has been deleted'.format(typeset.pk)
            )
            kwargs = {'typeset': typeset, 'request': request}
            event_logic.Events.raise_event(
                event_logic.Events.ON_TYPESET_TASK_DELETED,
                **kwargs
            )
            typeset.delete()
        elif 'update' in request.POST and typeset.accepted:
            messages.add_message(
                request,
                messages.WARNING,
                'This assignment has been accepted so cannot be edited.'
            )
        elif 'update' in request.POST:
            logic.update_typesetter_task(typeset, request)
        elif 'reset' in request.POST and typeset.status == 'declined':
            typeset.reset_task_dates()
        else:
            messages.add_message(
                request,
                messages.WARNING,
                '[{status}] An invalid operation has '
                'been attempted for this task.'.format(
                    status=typeset.friendly_status)
            )

        return redirect(
            reverse(
                'production_article',
                kwargs={'article_id': article.pk}
            )
        )

    template = 'production/edit_typesetter_assignment.html'
    context = {
        'typeset': typeset,
        'article': article,
    }

    return render(request, template, context)


@typesetter_user_required
def typesetter_requests(request, typeset_id=None, decision=None):
    """
    Allows Typesetters to view requests
    :param request: HttpRequest object
    :param typeset_id: TypesetTask object PK
    :param decision: string, 'accept' or 'decline'
    :return: HttpResponse
    """
    if typeset_id and decision:
        typeset_task = get_object_or_404(
            models.TypesetTask,
            pk=typeset_id,
            typesetter=request.user,
            assignment__article__journal=request.journal,
        )

        if decision == 'accept':
            typeset_task.accepted = timezone.now()
        elif decision == 'decline':
            typeset_task.accepted = None
            typeset_task.completed = timezone.now()

        typeset_task.save()

        kwargs = {'decision': decision, 'typeset_task': typeset_task, 'request': request}
        event_logic.Events.raise_event(event_logic.Events.ON_TYPESETTER_DECISION, **kwargs)
        return redirect(reverse('typesetter_requests'))

    typeset_tasks = models.TypesetTask.objects.filter(accepted__isnull=True,
                                                      completed__isnull=True,
                                                      typesetter=request.user,
                                                      assignment__article__journal=request.journal)

    in_progress_tasks = models.TypesetTask.objects.filter(accepted__isnull=False,
                                                          completed__isnull=True,
                                                          typesetter=request.user,
                                                          assignment__article__journal=request.journal)

    completed_tasks = models.TypesetTask.objects.filter(accepted__isnull=False,
                                                        completed__isnull=False,
                                                        typesetter=request.user,
                                                        assignment__article__journal=request.journal)

    template = 'production/typesetter_requests.html'
    context = {
        'typeset_tasks': typeset_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
    }

    return render(request, template, context)


@typesetter_or_editor_required
def do_typeset_task(request, typeset_id):
    """
    Displays a form for completing typeset tasks
    :param request: HttpRequest object
    :param typeset_id: TypesetTask object PK
    :return: HttpResponse or HttpRedirect
    """
    typeset_task = get_object_or_404(
        models.TypesetTask,
        pk=typeset_id,
        accepted__isnull=False,
        completed__isnull=True,
        assignment__article__journal=request.journal,
    )

    article = typeset_task.assignment.article
    galleys = core_models.Galley.objects.filter(article=article)
    form = forms.TypesetterNote(instance=typeset_task)

    if request.POST:

        if 'complete' in request.POST:
            form = forms.TypesetterNote(request.POST, instance=typeset_task)
            if form.is_valid():
                task = form.save()
                task.completed = timezone.now()
                task.save()

                kwargs = {
                    'typeset_task': typeset_task,
                    'request': request,
                }
                event_logic.Events.raise_event(
                    event_logic.Events.ON_TYPESET_COMPLETE,
                    **kwargs,
                )

                messages.add_message(
                    request,
                    messages.INFO,
                    'Typeset assignment complete.',
                )
                return redirect(reverse('typesetter_requests'))

        new_galley = None
        if 'file' in request.FILES:
            label = request.POST.get('label')
            for uploaded_file in request.FILES.getlist('file'):
                try:
                    new_galley = logic.save_galley(
                        article,
                        request,
                        uploaded_file,
                        True,
                        label=label,
                    )
                except UnicodeDecodeError:
                    messages.add_message(request, messages.ERROR,
                        "Uploaded file is not UTF-8 encoded")
                except logic.ZippedGalleyError:
                    messages.add_message(request, messages.ERROR,
                        "Galleys must be uploaded individually, not zipped",
                    )

        if 'source' in request.POST:
            for uploaded_file in request.FILES.getlist('source-file'):
                logic.save_source_file(
                    article,
                    request,
                    uploaded_file,
                )

        if new_galley:
            typeset_task.galleys_loaded.add(new_galley.file)

        if not request.FILES:
            messages.add_message(
                request,
                messages.WARNING,
                'No files uploaded.'
            )

        return redirect(reverse('do_typeset_task', kwargs={'typeset_id': typeset_task.pk}))

    manuscripts = article.manuscript_files.filter(is_galley=False)
    data_files = article.data_figure_files.filter(is_galley=False)
    copyedit_files = logic.get_copyedit_files(article)

    template = 'production/typeset_task.html'
    context = {
        'typeset_task': typeset_task,
        'article': article,
        'manuscripts': manuscripts,
        'data_files': data_files,
        'production_assignment': typeset_task.assignment,
        'copyedit_files': copyedit_files,
        'galleys': galleys,
        'form': form,
    }

    return render(request, template, context)


@typesetter_or_editor_required
def edit_galley(request, galley_id, typeset_id=None, article_id=None):
    """
    Allows a typesetter or editor to edit a Galley file.
    :param request: HttpRequest object
    :param galley_id: Galley object PK
    :param typeset_id: TypesetTask PK, optional
    :param article_id: Article PK, optional
    :return: HttpRedirect or HttpResponse
    """
    return_url = request.GET.get('return', None)

    if typeset_id:
        typeset_task = get_object_or_404(
            models.TypesetTask,
            pk=typeset_id,
            assignment__article__journal=request.journal,
            accepted__isnull=False,
            completed__isnull=True,
        )
        article = typeset_task.assignment.article
    else:
        typeset_task = None
        article = get_object_or_404(
            submission_models.Article.allarticles,
            pk=article_id,
            journal=request.journal
        )

    galley = get_object_or_404(
        core_models.Galley,
        pk=galley_id,
        article=article,
    )
    if galley.label == 'XML':
        xsl_files = core_models.XSLFile.objects.filter(
            Q(journal=request.journal)|Q(journal__isnull=True)
        )
    else:
        xsl_files = None

    if request.POST:

        if 'delete' in request.POST:
            if typeset_task:
                logic.handle_delete_request(
                    request,
                    galley,
                    typeset_task=typeset_task,
                    page="edit",
                )
                return redirect(
                    reverse(
                        'do_typeset_task',
                        kwargs={'typeset_id': typeset_task.pk},
                    )
                )
            else:
                logic.handle_delete_request(
                    request,
                    galley,
                    article=article,
                    page="pm_edit",
                )
                if not return_url:
                    return redirect(
                        reverse(
                            'production_article',
                            kwargs={'article_id': article.pk},
                        )
                    )
                else:
                    return redirect(return_url)

        label = request.POST.get('label')

        if 'fixed-image-upload' in request.POST:
            if request.POST.get('datafile') is not None:
                logic.use_data_file_as_galley_image(
                    galley,
                    request,
                    label,
                )
            for uploaded_file in request.FILES.getlist('image'):
                logic.save_galley_image(
                    galley,
                    request,
                    uploaded_file,
                    label,
                    fixed=True,
                )

        if 'image-upload' in request.POST:
            for uploaded_file in request.FILES.getlist('image'):
                logic.save_galley_image(
                    galley,
                    request,
                    uploaded_file,
                    label,
                    fixed=False,
                )

        elif 'css-upload' in request.POST:
            for uploaded_file in request.FILES.getlist('css'):
                logic.save_galley_css(
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
            logic.replace_galley_file(
                article, request,
                galley,
                request.FILES.get('galley'),
            )

        if 'xsl_file' in request.POST:
            xsl_file = get_object_or_404(core_models.XSLFile,
                    pk=request.POST["xsl_file"])
            galley.xsl_file = xsl_file
            galley.save()

        if typeset_task:
            return redirect(
                reverse(
                    'edit_galley',
                    kwargs={'typeset_id': typeset_id, 'galley_id': galley_id},
                )
            )
        else:
            return_path = '?return={return_url}'.format(
                return_url=return_url,
            ) if return_url else ''
            url = reverse(
                'pm_edit_galley',
                kwargs={'article_id': article.pk, 'galley_id': galley_id},
            )
            redirect_url = '{url}{return_path}'.format(
                url=url,
                return_path=return_path,
            )
            return redirect(redirect_url)

    template = 'production/edit_galley.html'
    context = {
        'typeset_task': typeset_task,
        'galley': galley,
        'article': galley.article,
        'image_names': logic.get_image_names(galley),
        'return_url': return_url,
        'data_files': article.data_figure_files.all(),
        'galley_images': galley.images.all(),
        'xsl_files': xsl_files,
    }

    return render(request, template, context)


@typesetter_or_editor_required
def upload_image_zip(request, galley_id, typeset_id=None, article_id=None):
    return_url = request.GET.get('return', None)

    if typeset_id:
        typeset_task = get_object_or_404(
            models.TypesetTask,
            pk=typeset_id,
            assignment__article__journal=request.journal,
            accepted__isnull=False,
            completed__isnull=True,
        )
        article = typeset_task.assignment.article
    else:
        typeset_task = None
        article = get_object_or_404(
            submission_models.Article.allarticles,
            pk=article_id,
            journal=request.journal
        )

    galley = get_object_or_404(
        core_models.Galley,
        pk=galley_id,
        article=article,
    )

    if request.POST and 'zip_file' in request.POST:
        file = request.FILES.get('file')
        try:
            logic.handle_zipped_galley_images(file, galley, request)
            return logic.edit_galley_redirect(
                typeset_task,
                galley,
                return_url,
                article,
            )
        except BadZipFile:
            messages.add_message(
                request,
                messages.ERROR,
                'File must be a .zip file.'
            )
            return logic.zip_redirect(typeset_id, article_id, galley_id)

    template = 'production/upload_image_zip.html'
    context = {
        'typeset_task': typeset_task,
        'galley': galley,
        'article': galley.article,
        'galley_images': galley.images.all(),
        'image_names': logic.get_image_names(galley),
        'return_url': return_url,
    }

    return render(request, template, context)


@production_user_or_editor_required
def review_typeset_task(request, article_id, typeset_id):
    """
    Allows an editor to view a Typeset task
    :param request: django request object
    :param article_id: Article PK
    :param typeset_id: TypesetTask PK
    :return: contextualised django template
    """
    typeset_task = get_object_or_404(models.TypesetTask, pk=typeset_id)
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    typeset_task.editor_reviewed = True
    typeset_task.save()

    return redirect(reverse('production_article', kwargs={'article_id': article.pk}))


@typesetter_or_editor_required
def delete_galley(request, typeset_id, galley_id):
    """
    Allows for deletion of a Galley
    :param request: HttpRequest object
    :param typeset_id: TypesetTask object PK
    :param galley_id: Galley object PK
    :return:
    """
    galley = get_object_or_404(
        core_models.Galley,
        pk=galley_id,
        article__journal=request.journal,
    )
    galley.file.unlink_file()
    galley.delete()

    return redirect(reverse('do_typeset_task', kwargs={'typeset_id': typeset_id}))


@production_user_or_editor_required
def supp_file_doi(request, article_id, supp_file_id):
    """
    Presents an interface for minting a supplementary file DOI
    :param request: HttpRequest
    :param article_id: Article object PK
    :param supp_file_id: SupplementaryFile PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    supplementary_file = get_object_or_404(
        core_models.SupplementaryFile,
        pk=supp_file_id,
    )
    test_mode = setting_handler.get_setting('Identifiers', 'crossref_test', article.journal).processed_value

    if not article.get_doi():
        messages.add_message(request, messages.INFO, 'Parent article must have a DOI before you can assign a'
                                                     'supplementary file a DOI.')

    xml_context = {'supp_file': supplementary_file,
                   'article': article,
                   'batch_id': uuid.uuid4(),
                   'timestamp': int(round((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())),
                   'depositor_name': setting_handler.get_setting('Identifiers', 'crossref_name',
                                                                 article.journal).processed_value,
                   'depositor_email': setting_handler.get_setting('Identifiers', 'crossref_email',
                                                                  article.journal).processed_value,
                   'registrant': setting_handler.get_setting('Identifiers', 'crossref_registrant',
                                                             article.journal).processed_value,
                   'parent_doi': article.get_doi()
                   }
    xml_content = render_to_string('admin/identifiers/crossref_component.xml', xml_context, request)

    if request.POST:
        from identifiers import logic
        logic.register_crossref_component(article, xml_content, supplementary_file)

        supplementary_file.doi = '{0}.{1}'.format(article.get_doi(), supplementary_file.pk)
        supplementary_file.save()
        return redirect(reverse('production_article', kwargs={'article_id': article.pk}))

    template = 'production/supp_file_doi.html'
    context = {
        'article': article,
        'supp_file': supplementary_file,
        'xml_content': xml_content,
        'test_mode': test_mode,
    }

    return render(request, template, context)

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from itertools import chain

from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse

from production import models
from core import files, models as core_models
from copyediting import models as copyediting_models
from utils import render_template


def get_production_managers(article):
    production_assignments = models.ProductionAssignment.objects.filter(article=article)
    production_managers = [assignment.copyeditor.pk for assignment in production_assignments]

    return core_models.AccountRole.objects.filter(role__slug='production').exclude(user__pk__in=production_managers)


def get_typesetters(article):
    typeset_assignments = models.TypesetTask.objects.filter(assignment__article=article,
                                                            completed__isnull=True)
    typesetters = [task.typesetter.pk for task in typeset_assignments]

    return core_models.AccountRole.objects.filter(role__slug='typesetter', journal=article.journal).exclude(
        user__pk__in=typesetters)


def get_all_galleys(article):
    return [galley for galley in article.galley_set.all()]


def save_prod_file(article, request, uploaded_file, label):
    new_file = files.save_file_to_article(uploaded_file, article, request.user)
    new_file.label = label
    new_file.is_galley = False
    new_file.save()

    article.manuscript_files.add(new_file)


def save_supp_file(article, request, uploaded_file, label):
    new_file = files.save_file_to_article(uploaded_file, article, request.user)
    new_file.label = label
    new_file.is_galley = False
    new_file.save()

    supp_file = core_models.SupplementaryFile.objects.create(file=new_file)

    article.supplementary_files.add(supp_file)


def save_galley(article, request, uploaded_file, is_galley, label, save_to_disk=True):
    new_file = files.save_file_to_article(uploaded_file, article, request.user, save=save_to_disk)
    new_file.is_galley = is_galley
    new_file.label = label

    new_file.save()
    article.save()

    if new_file.mime_type == 'text/html':
        type = 'html'
        label = 'HTML'
    elif new_file.mime_type == 'application/xml':
        type = 'xml'
        label = 'XML'
    else:
        type = label.lower()

    new_galley = core_models.Galley.objects.create(
        article=article, file=new_file, label=label, type=type, sequence=article.get_next_galley_sequence()
    )

    return new_galley


def replace_galley_file(article, request, galley, uploaded_file):
    if uploaded_file:
        new_file = files.save_file_to_article(uploaded_file, article, request.user)
        new_file.is_galley = True
        new_file.label = galley.file.label
        new_file.parent = galley.file
        new_file.save()
        galley.file = new_file
        galley.save()
    else:
        messages.add_message(request, messages.WARNING, 'No file was selected.')


def save_galley_image(galley, request, uploaded_file, label="Galley Image", fixed=False):

    if fixed:
        filename = request.POST.get('file_name')
        uploaded_file_mime = files.check_in_memory_mime(uploaded_file)
        expected_mime = files.guess_mime(filename)

        if not uploaded_file_mime == expected_mime:
            messages.add_message(request, messages.WARNING, 'The file you uploaded does not match the mime of the '
                                                            'file expected.')

    new_file = files.save_file_to_article(uploaded_file, galley.article, request.user)
    new_file.is_galley = False
    new_file.label = label

    if fixed:
        new_file.original_filename = request.POST.get('file_name')

    new_file.save()

    galley.images.add(new_file)

    return new_file


def use_data_file_as_galley_image(galley, request, label):
    file_id = request.POST.get('datafile')

    if file_id:
        try:
            file = core_models.File.objects.get(pk=file_id)
            file.original_filename = request.POST.get('file_name')
            file.save()
            galley.images.add(file)
            messages.add_message(request, messages.SUCCESS, 'File added.')
        except core_models.File.DoesNotExist:
            messages.add_message(request, messages.WARNING, 'No file with given ID found.')


def save_galley_css(galley, request, uploaded_file, filename, label="Galley Image"):
    new_file = files.save_file_to_article(uploaded_file, galley.article, request.user)
    new_file.is_galley = False
    new_file.label = label
    new_file.original_filename = filename
    new_file.save()

    galley.css_file = new_file
    galley.save()

    return new_file


def get_copyedit_files(article):
    c_files = []
    copyedits = copyediting_models.CopyeditAssignment.objects.filter(article=article)

    for copyedit in copyedits:
        for file in copyedit.copyeditor_files.all():
            c_files.append(file)

    return c_files


def handle_self_typesetter_assignment(production_assignment, request):
    user = get_object_or_404(core_models.Account, pk=request.POST.get('typesetter_id'))
    typeset_task = models.TypesetTask(
        assignment=production_assignment,
        typesetter=user,
        notified=True,
        accepted=timezone.now(),
        typeset_task='This is a self assignment.',
    )

    typeset_task.save()

    messages.add_message(request, messages.SUCCESS, 'You have been assigned as a typesetter to this article.')

    return typeset_task


def check_posted_typesetter_files(article, copyedit_files, posted_files):
    acceptable_file_list = list(
        chain(
            article.manuscript_files.all(),
            article.data_figure_files.all(),
            copyedit_files,
        )
    )

    if posted_files:
        for file in posted_files:
            if file not in acceptable_file_list:
                return False
    else:
        return False

    return True


def typesetter_users(typesetters):
    return [role.user for role in typesetters]


def update_typesetter_task(typeset, request):

    file_ints = request.POST.getlist('files', [])
    files = [core_models.File.objects.get(pk=f) for f in file_ints]

    for file in files:
        typeset.files_for_typesetting.add(file)

    for file in typeset.files_for_typesetting.all():
        if file not in files:
            typeset.files_for_typesetting.remove(file)

    typeset.typeset_task = request.POST.get('typeset_task', '')
    typeset.save()


def get_typesetter_notification(typeset_task, request):
    context = {
        'typeset_task': typeset_task,
    }
    return render_template.get_message_content(request, context, 'typesetter_notification')


def get_complete_template(request, article, production_assignment):
    context = {
        'article': article,
        'production_assignment': production_assignment,
    }
    return render_template.get_message_content(request, context, 'typeset_ack')


def get_image_names(galley):
    return [image.original_filename for image in galley.images.all()]


def handle_delete_request(request, galley, typeset_task=None, article=None, page=False):
    if typeset_task:
        article = typeset_task.assignment.article

    file_id = request.POST.get('delete', None)

    if file_id:
        try:
            file_to_delete = core_models.File.objects.get(pk=file_id)
            if file_to_delete.pk in galley.article.all_galley_file_pks():
                messages.add_message(request, messages.INFO, 'File deleted')

                # Check if this is a data file, and if it is remove it,
                # dont delete it.
                if file_to_delete in galley.article.data_figure_files.all():
                    galley.images.remove(file_to_delete)
                else:
                    file_to_delete.delete()
        except core_models.File.DoesNotExist:
            messages.add_message(request, messages.WARNING, 'File not found')

    if page == 'edit':
        return redirect(reverse('edit_galley', kwargs={'typeset_id': typeset_task.pk, 'galley_id': galley.pk}))
    elif page == 'pm_edit':
        return redirect(reverse('production_article', kwargs={'article_id': article.pk}))
    elif page == 'typeset':
        return redirect(reverse('do_typeset_task', kwargs={'typeset_id': typeset_task.pk}))
    else:
        return redirect(reverse('assigned_article', kwargs={'article_id': article.pk}))


def get_production_assign_content(user, request, article, url):
    context = {
        'user': user,
        'url': url,
        'article': article,
    }
    return render_template.get_message_content(request, context, 'production_assign_article')

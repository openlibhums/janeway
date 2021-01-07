__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from itertools import chain
import zipfile

from bs4 import BeautifulSoup
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.core.files.base import ContentFile

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


def save_source_file(article, request, uploaded_file):
    new_file = files.save_file_to_article(uploaded_file, article, request.user)
    new_file.label = "Source File"
    new_file.is_galley = False
    new_file.save()

    article.source_files.add(new_file)


def save_galley(article, request, uploaded_file, is_galley, label=None, save_to_disk=True):
    new_file = files.save_file_to_article(
        uploaded_file,
        article,
        request.user,
        save=save_to_disk,
    )
    new_file.is_galley = is_galley
    new_file.label = label

    new_file.save()
    article.save()

    type_ = None

    if new_file.mime_type in files.HTML_MIMETYPES:
        type_ = 'html'
        if not label:
            label = 'HTML'

        with open(new_file.self_article_path(), 'r+', encoding="utf-8") as f:
            html_contents = f.read()
            f.seek(0)
            cleaned_html = remove_css_from_html(html_contents)
            f.write(cleaned_html)
            f.truncate()

    elif new_file.mime_type in files.XML_MIMETYPES:
        type_ = 'xml'
        if not label:
            label = 'XML'
    elif new_file.mime_type in files.PDF_MIMETYPES:
        type_ = 'pdf'
        if not label:
            label = 'PDF'

    if not label:
        label = 'Other'
    if not type_:
        type_ = 'other'

    new_galley = core_models.Galley.objects.create(
        article=article,
        file=new_file,
        label=label,
        type=type_,
        sequence=article.get_next_galley_sequence(),
    )

    return new_galley


def remove_css_from_html(source_html):
    """ Removes any embedded css from the given html
    :param html: a str of containing html to be cleaned
    :return: A str with the cleaned html
    """
    soup = BeautifulSoup(source_html, "html.parser")
    # Remove external stylesheets
    link_tags = soup("link", {"rel": "stylesheet"})
    for link_tag in link_tags:
        link_tag.decompose()

    # Remove internal stylesheets
    style_tags = soup("style")
    for style_tag in style_tags:
        style_tag.decompose()

    # Remove internal stylesheets
    for tag in soup():
          del tag["style"]

    return soup.prettify()


def replace_galley_file(article, request, galley, uploaded_file):
    if uploaded_file:

        files.overwrite_file(
            uploaded_file,
            galley.file,
            ('articles', article.pk),
        )
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
        'typesetter_requests_url': request.journal.site_url(path=reverse('typesetter_requests')),
    }
    return render_template.get_message_content(request, context, 'typesetter_notification')


def get_complete_template(request, article, production_assignment):
    context = {
        'article': article,
        'production_assignment': production_assignment,
    }
    return render_template.get_message_content(request, context, 'production_complete')


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


def edit_galley_redirect(typeset_task, galley, return_url, article):
    if typeset_task:
        return redirect(
            reverse(
                'edit_galley',
                kwargs={'typeset_id': typeset_task.pk, 'galley_id': galley.pk},
            )
        )
    else:
        return_path = '?return={return_url}'.format(
            return_url=return_url,
        ) if return_url else ''
        url = reverse(
            'pm_edit_galley',
            kwargs={'article_id': article.pk, 'galley_id': galley.pk},
        )
        redirect_url = '{url}{return_path}'.format(
            url=url,
            return_path=return_path,
        )
        return redirect(redirect_url)


def zip_redirect(typeset_id, article_id, galley_id):
    if typeset_id:
        return redirect(
            reverse(
                'typesetter_zip_uploader',
                kwargs={
                    'typeset_id': typeset_id,
                    'galley_id': galley_id,
                }
            )
        )
    else:
        return redirect(
            reverse(
                'pm_zip_uploader',
                kwargs={
                    'article_id': article_id,
                    'galley_id': galley_id
                }
            )
        )


def handle_zipped_galley_images(zip_file, galley, request):

    with zipfile.ZipFile(zip_file, 'r') as zf:
        for finfo in zf.infolist():
            zipped_file = zf.open(finfo)
            content_file = ContentFile(zipped_file.read())
            content_file.name = zipped_file.name

            if zipped_file.name in galley.has_missing_image_files():
                new_file = files.save_file_to_article(
                    content_file,
                    galley.article,
                    request.user,
                )
                new_file.is_galley = False
                new_file.label = "Galley Image"
                new_file.save()

                galley.images.add(new_file)

            elif zipped_file.name in galley.all_images():
                try:
                    file = galley.images.get(
                        original_filename=zipped_file.name,
                    )

                    updated_file = files.overwrite_file(
                        content_file,
                        file,
                        ('articles', galley.article.pk)
                    )
                    updated_file.original_filename = zipped_file.name
                    updated_file.save()

                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        'New version of {} saved.'.format(zipped_file.name)
                    )
                except core_models.File.DoesNotExist:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        'A file was found in XML and Zip but no corresponding'
                        'File object could be found. {}'.format(
                            zipped_file.name,
                        )
                    )

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    ''
                )
            else:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'File {} not found in XML'.format(zipped_file.name)
                )
    return

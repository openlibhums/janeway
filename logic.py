from django.contrib import messages

from production import logic
from core import models as core_models, files
from utils import render_template


def production_ready_files(article, file_objects=False):
    """
    Gathers a list of production ready files.
    :param article: an Article object
    :param file_objects: Boolean
    :return: a list of File type objects
    """
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
    context = {
        'article': article,
        'assignment': assignment,
    }
    return render_template.get_message_content(
        request,
        context,
        'typesetting_notify_typesetter',
    )


def get_proofreader_notification(assignment, article, request):
    context = {
        'article': article,
        'assignment': assignment,
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
                'Annotated file uploaded.',
            )



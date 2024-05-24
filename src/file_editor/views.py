from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib import messages

from core import models as core_models, files
from file_editor import forms
from security.decorators import editor_user_required, has_journal


@has_journal
@editor_user_required
def galley_list(request):
    galleys = core_models.Galley.objects.filter(
        article__journal=request.journal,
        file__mime_type__in=files.MIMETYPES_WITH_FIGURES,
    ).select_related(
        'article',
    )
    template = 'admin/editors/galley_list.html'
    context = {
        'galleys': galleys,
    }
    return render(
        request,
        template,
        context
    )


@has_journal
@editor_user_required
def edit_galley_file(request, article_id, galley_id):
    """
    Allows and editor user to view and edit the contents of a galley file.
    :param request: HttpRequest object
    :param galley_id: int Galley object primary key
    """
    galley = get_object_or_404(
        core_models.Galley,
        pk=galley_id,
        article__pk=article_id,
        article__journal=request.journal,
    )
    warning = None
    if not galley.file:
        warning = 'Galley has no corresponding file object'
    elif galley.file.mime_type not in files.MIMETYPES_WITH_FIGURES:
        warning = 'This file type is not editable.'
    if warning:
        messages.add_message(request, messages.WARNING, warning)
        return redirect(reverse('editor_galley_list'))

    form = forms.GalleyEditForm(
        galley=galley,
    )
    if request.POST:
        form = forms.GalleyEditForm(
            request.POST,
            galley=galley,
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Galley content saved.',
            )
            return redirect(
                reverse(
                    'editors_edit_galley_file',
                    kwargs={
                        'article_id': galley.article.pk,
                        'galley_id': galley.pk,
                    }
                )
            )

    template = 'admin/editors/edit_galley_file.html'
    context = {
        'galley': galley,
        'form': form,
    }
    return render(
        request,
        template,
        context
    )

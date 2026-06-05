__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _

from copyediting import forms, logic, models
from core import files
from security.decorators import editor_user_required
from submission import models as submission_models
from utils.htmx import hx_redirect


@editor_user_required
def upload_editor_version(request, article_id):
    """
    Allows an editor to upload their own copyedited file, shorthand-creating
    a completed CopyeditAssignment ready for author review.
    :param request: HttpRequest object
    :param article_id: a submission.models.Article PK
    :return: an HTMX modal form partial, or an HX-Redirect to editor_review
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    form = forms.EditorVersionForm()

    if request.POST:
        form = forms.EditorVersionForm(request.POST, request.FILES)
        if form.is_valid():
            copyedit = logic.create_complete_copyedit_assignment(
                article,
                request.user,
            )
            new_file = files.save_file_to_article(
                form.cleaned_data["file"],
                article,
                request.user,
                label=form.cleaned_data["label"],
            )
            copyedit.copyeditor_files.add(new_file)
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Editor version uploaded and copyedit assignment created."),
            )
            return hx_redirect(
                reverse(
                    "editor_review",
                    kwargs={
                        "article_id": article.pk,
                        "copyedit_id": copyedit.pk,
                    },
                )
            )

    template = "admin/copyediting/partials/upload_editor_version_form.html"
    context = {
        "article": article,
        "form": form,
    }

    return render(request, template, context)


@editor_user_required
def request_author_version(request, article_id):
    """
    Allows an editor to ask the author for a new version of their manuscript,
    shorthand-creating a completed CopyeditAssignment and an AuthorReview,
    then handing off to the existing request_author_copyedit notification step.
    :param request: HttpRequest object
    :param article_id: a submission.models.Article PK
    :return: an HTMX modal form partial, or an HX-Redirect to
    request_author_copyedit
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    author = article.correspondence_author
    article_files = article.manuscript_files.all() | article.data_figure_files.all()
    form = forms.RequestAuthorVersionForm(files=article_files)

    if request.POST and author:
        form = forms.RequestAuthorVersionForm(request.POST, files=article_files)
        if form.is_valid():
            copyedit = logic.create_complete_copyedit_assignment(
                article,
                request.user,
            )
            selected_files = form.cleaned_data["files"]
            copyedit.files_for_copyediting.add(*selected_files)

            # Adding the files as copyeditor files lets the author replace
            # them with new versions via the author_update_file view.
            copyedit.copyeditor_files.add(*selected_files)
            author_review = models.AuthorReview.objects.create(
                author=author,
                assignment=copyedit,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Copyedit assignment and author review task created."),
            )
            return hx_redirect(
                reverse(
                    "request_author_copyedit",
                    kwargs={
                        "article_id": article.pk,
                        "copyedit_id": copyedit.pk,
                        "author_review_id": author_review.pk,
                    },
                )
            )

    template = "admin/copyediting/partials/request_author_version_form.html"
    context = {
        "article": article,
        "author": author,
        "form": form,
    }

    return render(request, template, context)

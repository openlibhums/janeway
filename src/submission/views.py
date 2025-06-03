__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone, translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import PermissionDenied

from core import files, models as core_models
from core.logic import create_organization_name, reverse_with_next
from core.views import GenericFacetedListView
from core.forms import (
    AccountAffiliationForm,
    ConfirmDeleteForm,
    OrcidAffiliationForm,
    OrganizationNameForm,
)
from repository import models as preprint_models
from security.decorators import (
    article_edit_user_required,
    production_user_or_editor_required,
    editor_user_required,
    submission_authorised,
    article_is_not_submitted,
    role_can_access,
)
from submission import forms, models, logic, decorators
from events import logic as event_logic
from utils import setting_handler
from utils import shared as utils_shared, orcid
from utils.forms import clean_orcid_id
from utils.decorators import GET_language_override
from utils.shared import create_language_override_redirect


@login_required
@decorators.submission_is_enabled
@submission_authorised
def start(request, type=None):
    """
    Starts the submission process, presents various checkboxes
    and then creates a new article.
    :param request: HttpRequest object
    :param type: string, None or 'preprint'
    :return: HttpRedirect or HttpResponse
    """
    form = forms.ArticleStart(journal=request.journal)

    if not request.user.is_author(request):
        request.user.add_account_role('author', request.journal)

    if request.POST:
        form = forms.ArticleStart(request.POST, journal=request.journal)

        if form.is_valid():
            new_article = form.save(commit=False)
            new_article.owner = request.user
            new_article.journal = request.journal
            new_article.current_step = 1
            new_article.article_agreement = logic.get_agreement_text(request.journal)
            new_article.save()

            if type == 'preprint':
                preprint_models.Preprint.objects.create(article=new_article)

            new_article.correspondence_author = request.user
            new_article.save()
            request.user.snapshot_self(new_article)

            event_logic.Events.raise_event(
                event_logic.Events.ON_ARTICLE_SUBMISSION_START,
                **{'request': request, 'article': new_article}
            )

            return redirect(
                reverse(
                    'submit_info',
                    kwargs={
                        'article_id': new_article.pk},
                ),
            )

    template = 'admin/submission/start.html'
    context = {
        'form': form
    }

    return render(request, template, context)


@login_required
@decorators.submission_is_enabled
def submit_submissions(request):
    """Displays a list of submissions made by the author."""
    # gets a list of submissions for the logged in user
    articles = models.Article.objects.filter(
        owner=request.user,
        journal=request.journal,
    ).exclude(
        stage=models.STAGE_UNSUBMITTED,
    )

    template = 'admin/submission/submission_submissions.html'
    context = {
        'articles': articles,
    }

    return render(request, template, context)


@login_required
@decorators.submission_is_enabled
@decorators.funding_is_enabled
@article_is_not_submitted
@article_edit_user_required
@submission_authorised
def submit_funding(request, article_id):
    """
    Presents a form for the user to complete with article information
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    additional_fields = models.Field.objects.filter(journal=request.journal)
    funder_form = forms.ArticleFundingForm(
        article=article,
    )

    if request.POST:
        if 'next_step' in request.POST:
            article.current_step = 5
            article.save()
            return redirect(reverse('submit_review', kwargs={'article_id': article_id}))

        funder_form = forms.ArticleFundingForm(
            request.POST,
            article=article,
        )

        if funder_form.is_valid():
            funder_form.save()
            return redirect(
                reverse(
                    'submit_funding',
                    kwargs={
                        'article_id': article.pk,
                    }
                )
            )

    template = 'admin/submission/submit_funding.html'
    context = {
        'article': article,
        'additional_fields': additional_fields,
        'funder_form': funder_form,
    }

    return render(request, template, context)


@login_required
@decorators.submission_is_enabled
@article_is_not_submitted
@article_edit_user_required
@submission_authorised
def submit_info(request, article_id):
    """
    Presents a form for the user to complete with article information
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse or HttpRedirect
    """
    with translation.override(settings.LANGUAGE_CODE):
        article = get_object_or_404(
            models.Article,
            pk=article_id,
            journal=request.journal,
        )
        additional_fields = models.Field.objects.filter(journal=request.journal)
        submission_summary = setting_handler.get_setting(
            'general',
            'submission_summary',
            request.journal,
        ).processed_value

        # Determine the form to use depending on whether the user is an editor.
        article_info_form = forms.ArticleInfoSubmit
        if request.user.is_editor(request):
            article_info_form = forms.EditorArticleInfoSubmit

        form = article_info_form(
            instance=article,
            additional_fields=additional_fields,
            submission_summary=submission_summary,
            journal=request.journal,
        )

        if request.POST:
            form = article_info_form(
                request.POST,
                instance=article,
                additional_fields=additional_fields,
                submission_summary=submission_summary,
                journal=request.journal,
            )
            if form.is_valid():
                form.save(request=request)

                article.current_step = 2
                article.save()

                return redirect(
                    reverse(
                        'submit_authors',
                        kwargs={'article_id': article_id},
                    ),
                )

    template = 'admin/submission//submit_info.html'
    context = {
        'article': article,
        'form': form,
        'additional_fields': additional_fields,
    }

    return render(request, template, context)


@staff_member_required
def publisher_notes_order(request, article_id):
    if request.POST:
        ids = request.POST.getlist('note[]')
        ids = [int(_id) for _id in ids]

        article = models.Article.objects.get(
            pk=article_id,
            journal=request.journal,
        )

        for he in article.publisher_notes.all():
            he.sequence = ids.index(he.pk)
            he.save()

    return HttpResponse('Thanks')


@login_required
@decorators.submission_is_enabled
@article_is_not_submitted
@article_edit_user_required
@submission_authorised
def submit_authors(request, article_id):
    """
    Allows the submitting author to add other authors to the submission.
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpRedirect or HttpResponse
    """
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )

    if article.current_step < 2 and not request.user.is_staff:
        return redirect(
            reverse('submit_info', kwargs={'article_id': article_id}
        )
    )

    new_author_form = forms.EditFrozenAuthor()
    last_changed_author = None

    if request.POST and 'add_author' in request.POST:
        new_author_form = forms.EditFrozenAuthor(request.POST)

        frozen_email = request.POST.get("frozen_email")
        try:
            author = models.FrozenAuthor.objects.get(
                Q(article=article) &
                (Q(frozen_email=frozen_email) |
                Q(author__username__iexact=frozen_email))
            )
        except models.FrozenAuthor.DoesNotExist:
            author = None

        if not author and new_author_form.is_valid():
            author = new_author_form.save()
            author.article = article
            author.order = article.next_frozen_author_order()
            author.save()
            new_author_form = forms.EditFrozenAuthor()
        else:
            messages.add_message(
                request, messages.WARNING,
                _('Could not add the author manually.'),
            )

        if author:
            messages.add_message(
                request, messages.SUCCESS,
                _('%(author_name)s (%(email)s) added to the article.')
                    % {
                        "author_name": author.full_name(),
                        "email": author.email
                    },
            )
        last_changed_author = author

    elif request.POST and 'search_authors' in request.POST:
        search_term = request.POST.get('author_search_text')
        author = logic.add_author_from_search(search_term, request, article)
        last_changed_author = author

    elif request.POST and 'corr_author' in request.POST:
        account = get_object_or_404(
            core_models.Account,
            pk=request.POST.get('corr_author', None),
            frozenauthor__article=article,
        )
        article.correspondence_author = account
        article.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            _('%(author_name)s (%(email)s) made correspondence author.')
                % {
                    "author_name": account.full_name(),
                    "email": account.email
                },
        )
        last_changed_author = account.frozen_author(article)

    elif request.POST and 'change_order' in request.POST:
        last_changed_author = logic.save_frozen_author_order(request, article)

    elif request.POST and 'save_continue' in request.POST:

        if not article.correspondence_author:
            messages.add_message(
                request,
                messages.WARNING,
                _('The article does not have a correspondence author. '
                  'Please select a correspondence author to continue.'),
            )
            return redirect(
                reverse(
                    'submit_authors',
                    kwargs={'article_id': article_id}
                )
            )

        article.current_step = 3
        article.save()
        return redirect(
            reverse(
                'submit_files',
                kwargs={'article_id': article_id}
            )
        )

    template = 'admin/submission/submit_authors.html'
    context = {
        'article': article,
        'last_changed_author': last_changed_author,
        'new_author_form': new_author_form,
    }

    return render(request, template, context)


@login_required
@article_edit_user_required
@decorators.funding_is_enabled
def edit_funder(request, article_id, funder_id):
    """
    Allows staff, editor or article owner to edit a funding entry.
    :param request: HttpRequest object
    :param article_id: Article primary key
    :param funder_id: Funder primary key
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    funder = get_object_or_404(
        article.funders,
        pk=funder_id,
    )
    form = forms.ArticleFundingForm(
        instance=funder,
        article=article,
    )
    # If the user is not an editor/section editor/journal manager/staff
    # and the article is submitted we should raise PermissionDenied.
    if article.date_submitted and not request.user.has_an_editor_role(request):
        raise PermissionDenied(
            'This article has been submitted and cannot be edited.'
        )

    if request.POST:
        form = forms.ArticleFundingForm(
            request.POST,
            instance=funder,
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Article funding information saved.',
            )
            # The incoming link _should_ have a return value set to ensure
            # the user gets back to the right place.
            if request.GET.get('return'):
                return redirect(request.GET['return'])

            # If no return value is set we should try to work out where the
            # user should be sent to.
            if not article.date_submitted and article.owner == request.user:
                # In this case, the article is not submitted and the current
                # user is the owner, it's likely the user came from submission.
                return redirect(
                    reverse(
                        'submit_funding',
                        kwargs={
                            'article_id': article.pk,
                        }
                    )
                )
            else:
                return redirect(
                    reverse(
                        'edit_metadata',
                        kwargs={
                            'article_id': article.pk,
                        }
                    )
                )

    template = 'admin/submission/edit/funder.html'
    context = {
        'article': article,
        'funder': funder,
        'form': form,
    }
    return render(
        request,
        template,
        context,
    )


@login_required
@decorators.funding_is_enabled
@article_edit_user_required
def delete_funder(request, article_id, funder_id):
    """Allows submitting author to delete a funding object."""
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal
    )
    article_funding = get_object_or_404(
        models.ArticleFunding,
        pk=funder_id,
        article=article,
    )

    article_funding.delete()

    if request.GET.get('return'):
        return redirect(request.GET['return'])

    return redirect(reverse('submit_funding', kwargs={'article_id': article_id}))


@login_required
@article_edit_user_required
def delete_author(request, article_id, author_id):
    """Allows submitting author to remove an author from their article."""
    raise DeprecationWarning("Use delete_frozen_author instead.")
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal
    )
    author = get_object_or_404(
        core_models.Account,
        pk=author_id
    )
    if author == article.correspondence_author:
        possible_corr_authors = [
            order.author for order in article.articleauthororder_set.exclude(
                author__email__endswith=settings.DUMMY_EMAIL_DOMAIN,
            ).exclude(
                author__pk=author.pk,
            )
        ]
        if possible_corr_authors:
            article.correspondence_author = possible_corr_authors[0]
            article.save()
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _('%(author_name)s (%(email)s) is the only possible '
                  'correspondence author. Please add another author '
                  'with an email address before removing %(author_name)s.')
                    % {
                        "author_name": author.full_name(),
                        "email": author.email
                    },
            )
            return redirect(
                reverse(
                    'submit_authors',
                    kwargs={'article_id': article_id}
                )
            )

    article.authors.remove(author)
    try:
        ordering = models.ArticleAuthorOrder.objects.get(
            article=article,
            author=author,
        ).delete()
    except models.ArticleAuthorOrder.DoesNotExist:
        pass
    messages.add_message(
        request,
        messages.INFO,
        _('%(author_name)s (%(email)s) removed from the article.')
            % {
                "author_name": author.full_name(),
                "email": author.email
            },
    )
    return redirect(reverse('submit_authors', kwargs={'article_id': article_id}))


@login_required
@article_edit_user_required
def delete_frozen_author(request, article_id, author_id):
    """
    Allows the article owner or editor to
    remove a frozen author from the article.
    """

    next_url = request.GET.get('next', '')
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal
    )
    author = get_object_or_404(
        models.FrozenAuthor,
        pk=author_id,
        article=article,
    )
    form = ConfirmDeleteForm()

    possible_corr_authors = models.FrozenAuthor.objects.filter(
        article=article,
        author__isnull=False,
    ).exclude(
        author__email__endswith=settings.DUMMY_EMAIL_DOMAIN,
    ).exclude(
        pk=author.pk,
    )
    if not possible_corr_authors.exists():
        messages.add_message(
            request,
            messages.ERROR,
            _('%(author_name)s (%(email)s) is the only possible '
              'correspondence author. Please add another author '
              'who has a user account before removing %(author_name)s.')
                % {
                    "author_name": author.full_name(),
                    "email": author.email
                },
        )
        return redirect(
            reverse_with_next(
                'submit_authors',
                next_url,
                kwargs={'article_id': article_id}
            )
        )

    if request.method == 'POST':
        form = ConfirmDeleteForm(request.POST)
        if form.is_valid() and possible_corr_authors.exists():
            if author.is_correspondence_author:
                article.correspondence_author = possible_corr_authors.first().author
                article.save()
            author.delete()
            messages.add_message(
                request,
                messages.INFO,
                _('%(author_name)s (%(email)s) is no longer an author.')
                    % {
                        "author_name": author.full_name(),
                        "email": author.email
                    },
            )
            if next_url:
                return redirect(next_url)
            else:
                return redirect(
                    reverse(
                        'submit_authors',
                        kwargs={'article_id': article_id}
                    )
                )

    template = 'admin/submission/edit/author_confirm_delete.html'
    context = {
        'article': article,
        'author': author,
        'form': form,
        'thing_to_delete': author,
    }
    return render(request, template, context)


@login_required
@decorators.submission_is_enabled
@article_is_not_submitted
@article_edit_user_required
@submission_authorised
def submit_files(request, article_id):
    """
    Allows the submitting author to upload files and links them to the submission
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse
    """
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    ms_form = forms.FileDetails(
        initial={
            "label": article.journal.submissionconfiguration.submission_file_text,
        },
    )
    data_form = forms.FileDetails(
        initial={
            "label": "Figure/Data File",
        },
    )
    configuration = request.journal.submissionconfiguration

    if article.current_step < 3 and not request.user.is_staff:
        return redirect(reverse('submit_authors', kwargs={'article_id': article_id}))

    error, modal = None, None

    if request.POST:

        if 'delete' in request.POST:
            file_id = request.POST.get('delete')
            file = get_object_or_404(core_models.File, pk=file_id, article_id=article.pk)
            file.delete()
            messages.add_message(
                request,
                messages.WARNING,
                _('File deleted'),
            )
            return redirect(reverse('submit_files', kwargs={'article_id': article_id}))

        if 'manuscript' in request.POST:
            ms_form = forms.FileDetails(request.POST)
            uploaded_file = request.FILES.get('file')
            if logic.check_file(uploaded_file, request, ms_form):
                if ms_form.is_valid():
                    new_file = files.save_file_to_article(
                        uploaded_file,
                        article,
                        request.user,
                    )
                    article.manuscript_files.add(new_file)
                    new_file.label = ms_form.cleaned_data['label']
                    new_file.description = ms_form.cleaned_data['description']
                    new_file.save()
                    return redirect(
                        reverse('submit_files', kwargs={'article_id': article_id}),
                    )
                else:
                    modal = 'manuscript'
            else:
                modal = 'manuscript'

        if 'data' in request.POST:
            data_form = forms.FileDetails(request.POST)
            uploaded_file = request.FILES.get('file')
            if data_form.is_valid() and uploaded_file:
                new_file = files.save_file_to_article(
                    uploaded_file,
                    article,
                    request.user,
                )
                article.data_figure_files.add(new_file)
                new_file.label = data_form.cleaned_data['label']
                new_file.description = data_form.cleaned_data['description']
                new_file.save()
                return redirect(reverse('submit_files', kwargs={'article_id': article_id}))
            else:
                data_form.add_error(None, 'You must select a file.')
                modal = 'data'

        if 'next_step' in request.POST:
            if article.manuscript_files.all().count() >= 1:
                article.current_step = 4
                article.save()
                if configuration.funding:
                    return redirect(reverse(
                        'submit_funding', kwargs={'article_id': article_id}))
                else:
                    return redirect(reverse(
                        'submit_review', kwargs={'article_id': article_id}))
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("You must upload a manuscript file.")
                )

    template = "admin/submission/submit_files.html"

    context = {
        'article': article,
        'ms_form': ms_form,
        'data_form': data_form,
        'modal': modal,
    }

    return render(request, template, context)


@login_required
@decorators.submission_is_enabled
@article_is_not_submitted
@article_edit_user_required
@submission_authorised
def submit_review(request, article_id):
    """
    A page that allows the user to review a submission.
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )

    if article.current_step < 4 and not request.user.is_staff:
        return redirect(
            reverse(
                'submit_info',
                kwargs={'article_id': article_id},
            )
        )
    form = forms.SubmissionCommentsForm(
        instance=article,
    )

    if request.POST and 'next_step' in request.POST:
        form = forms.SubmissionCommentsForm(
            request.POST,
            instance=article,
        )
        if form.is_valid():
            form.save()
            article.date_submitted = timezone.now()
            article.stage = models.STAGE_UNASSIGNED
            article.current_step = 5
            article.save()

            event_logic.Events.raise_event(
                event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE,
                **{'handshake_url': 'submit_review',
                   'request': request,
                   'article': article,
                   'switch_stage': False}
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                _('Article {title} submitted').format(
                    title=article.title,
                ),
            )

            kwargs = {'article': article,
                      'request': request}
            event_logic.Events.raise_event(
                event_logic.Events.ON_ARTICLE_SUBMITTED,
                task_object=article,
                **kwargs
            )

            return redirect(reverse('core_dashboard'))

    template = "admin/submission/submit_review.html"
    context = {
        'article': article,
        'form': form,
    }

    return render(request, template, context)


@GET_language_override
@production_user_or_editor_required
def edit_metadata(request, article_id):
    """
    Allows the Editors and Production Managers to edit an Article's metadata/
    :param request: request object
    :param article_id: PK of an Article
    :return: contextualised django template
    """
    with translation.override(request.override_language):
        article = get_object_or_404(
            models.Article,
            pk=article_id,
            journal=request.journal,
        )
        additional_fields = models.Field.objects.filter(
            journal=request.journal,
        )
        submission_summary = setting_handler.get_setting(
            'general',
            'submission_summary',
            request.journal,
        ).processed_value
        funder_form = forms.ArticleFundingForm(
            article=article,
        )

        info_form = forms.EditArticleMetadata(
            instance=article,
            additional_fields=additional_fields,
            submission_summary=submission_summary,
            pop_disabled_fields=False,
            editor_view=True,
        )

        return_param = request.GET.get('return')
        reverse_url = create_language_override_redirect(
            request,
            'edit_metadata',
            {'article_id': article.pk},
            query_strings={'return': return_param}
        )

        frozen_author, modal, author_form = None, None, forms.EditFrozenAuthor()
        if request.GET.get('author'):
            frozen_author, modal = logic.get_author(request, article)
            author_form = forms.EditFrozenAuthor(instance=frozen_author)
        elif request.GET.get('modal') == 'author':
            modal = 'author'

        if request.POST:
            if 'add_funder' in request.POST:
                funder_form = forms.ArticleFundingForm(
                    request.POST,
                    article=article,
                )
                if funder_form.is_valid():
                    funder_form.save()
                    return redirect(reverse_url)

            if 'metadata' in request.POST:
                info_form = forms.EditArticleMetadata(
                    request.POST,
                    instance=article,
                    additional_fields=additional_fields,
                    submission_summary=submission_summary,
                    pop_disabled_fields=False,
                    editor_view=True,
                )

                if info_form.is_valid():
                    info_form.save(request=request)
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        _('Metadata updated.'),
                    )
                    return redirect(reverse_url)

            if 'mark_primary' in request.POST and frozen_author.author:
                article.correspondence_author = frozen_author.author
                article.save()
                frozen_author.display_email = True
                frozen_author.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _('Correspondence author set.')
                )
                return redirect(reverse_url)

            if 'author' in request.POST:
                author_form = forms.EditFrozenAuthor(
                    request.POST,
                    instance=frozen_author,
                )

                if author_form.is_valid():
                    saved_author = author_form.save()
                    saved_author.article = article
                    saved_author.save()
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        _('Author {author_name} updated.').format(
                            author_name=saved_author.full_name(),
                        ),
                    )
                    return redirect(reverse_url)

            if 'delete' in request.POST:
                frozen_author_id = request.POST.get('delete')
                frozen_author = get_object_or_404(
                    models.FrozenAuthor,
                    pk=frozen_author_id,
                    article=article,
                    article__journal=request.journal,
                )
                frozen_author.delete()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _('Frozen Author deleted.'),
                )
                return redirect(reverse_url)

    template = 'submission/edit/metadata.html'
    context = {
        'article': article,
        'funder_form': funder_form,
        'info_form': info_form,
        'author_form': author_form,
        'modal': modal,
        'frozen_author': frozen_author,
        'additional_fields': additional_fields,
        'return': return_param
    }

    return render(request, template, context)


@login_required
@article_edit_user_required
def edit_author(request, article_id, author_id):
    """
    Allows a submitting author to edit an author record
    if they are the article owner or they are the author.
    :param request: request object
    :param article_id: PK of an Article
    :param frozen_author_id: PK of a FrozenAuthor
    :return: contextualised django template
    """
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    author = get_object_or_404(
        models.FrozenAuthor,
        Q(pk=author_id) &
        Q(article=article) &
        (Q(author=request.user) |
        Q(article__owner=request.user))
    )
    next_url = request.GET.get('next_url', '')
    form = None
    use_credit = setting_handler.get_setting(
        "general",
        "use_credit",
        journal=request.journal,
    ).processed_value
    if use_credit:
        credit_form = forms.CreditRecordForm(
            frozen_author=author,
        )
    else:
        credit_form = None

    if request.method == 'GET' and 'edit_author' in request.GET:
        form = forms.EditFrozenAuthor(instance=author)
        messages.add_message(
            request,
            messages.WARNING,
            _('You are editing the name, bio, and identifiers for %(author_name)s. '
              'Select "Save" when you are finished editing.')
                % {
                    "author_name": author.full_name(),
                },
        )

    elif request.method == 'POST' and 'save_author' in request.POST:
        form = forms.EditFrozenAuthor(
            request.POST,
            instance=author,
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _('Name, bio, and identifiers saved.'),
            )
            return redirect(
                reverse_with_next(
                    'submission_edit_author',
                    next_url,
                    kwargs={
                        'article_id': article.pk,
                        'author_id': author.pk,
                    }
                )
            )

    elif request.method == 'POST' and 'add_credit' in request.POST:
        credit_form = forms.CreditRecordForm(request.POST)
        if credit_form.is_valid() and author:
            record = credit_form.save()
            record.frozen_author = author
            record.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _('%(author_name)s now has role %(role)s.')
                    % {
                        "author_name": author.full_name(),
                        "role": record.get_role_display(),
                    },
            )
            return redirect(
                reverse_with_next(
                    'submission_edit_author',
                    next_url,
                    kwargs={
                        'article_id': article.pk,
                        'author_id': author.pk,
                    }
                )
            )

    elif request.method == 'POST' and 'remove_credit' in request.POST:
        record = get_object_or_404(
            models.CreditRecord,
            pk=int(request.POST.get('credit_pk')),
            frozen_author__article=article,
        )
        author = record.frozen_author
        role_display = record.get_role_display()
        record.delete()
        messages.add_message(
            request,
            messages.SUCCESS,
            _('%(author_name)s no longer has the role %(role)s.')
                % {
                    "author_name": author.full_name(),
                    "role": role_display,
                },
        )
        return redirect(
            reverse_with_next(
                'submission_edit_author',
                next_url,
                kwargs={
                    'article_id': article.pk,
                    'author_id': author.pk,
                }
            )
        )

    template = 'admin/submission/edit/author.html'
    context = {
        'article': article,
        'author': author,
        'form': form,
        'credit_form': credit_form,
    }

    return render(request, template, context)


@production_user_or_editor_required
def order_authors(request, article_id):
    article = get_object_or_404(models.Article, pk=article_id, journal=request.journal)

    if request.POST:
        ids = [int(_id) for _id in request.POST.getlist('authors[]')]

        for author in article.frozenauthor_set.all():
            order = ids.index(author.pk)
            author.order = order
            author.save()

    return HttpResponse('Thanks')


@editor_user_required
def fields(request, field_id=None):
    """
    Allows the editor to create, edit and delete new submission fields.
    :param request: HttpRequest object
    :param field_id: Field object PK, optional
    :return: HttpResponse or HttpRedirect
    """

    field = logic.get_current_field(request, field_id)
    fields = logic.get_submission_fields(request)
    form = forms.FieldForm(instance=field)

    if request.POST:

        if 'save' in request.POST:
            form = forms.FieldForm(request.POST, instance=field)

            if form.is_valid():
                logic.save_field(request, form)
                return redirect(reverse('submission_fields'))

        elif 'delete' in request.POST:
            logic.delete_field(request)
            return redirect(reverse('submission_fields'))

        elif 'order[]' in request.POST:
            logic.order_fields(request, fields)
            return HttpResponse('Thanks')

    template = 'admin/submission/manager/fields.html'
    context = {
        'field': field,
        'fields': fields,
        'form': form,
    }

    return render(request, template, context)


@role_can_access('licenses')
def licenses(request, license_pk=None):
    """
    Allows an editor to create, edit and delete license objects.
    :param request: HttpRequest object
    :param license_pk: License object PK, optional
    :return: HttResponse or HttpRedirect
    """
    license_obj = None
    licenses = models.Licence.objects.filter(journal=request.journal)

    if license_pk and request.journal:
        license_obj = get_object_or_404(
            models.Licence,
            journal=request.journal,
            pk=license_pk
        )
    elif license_pk and request.press:
        license_obj = get_object_or_404(
            models.Licence,
            press=request.press,
            pk=license_pk
        )

    form = forms.LicenseForm(instance=license_obj)

    if request.POST and 'save' in request.POST:
        form = forms.LicenseForm(request.POST,
                                 instance=license_obj)

        if form.is_valid():
            save_license = form.save(commit=False)
            if request.journal:
                save_license.journal = request.journal
            else:
                save_license.press = request.press

            save_license.save()
            messages.add_message(
                request,
                messages.INFO,
                _('License saved.'),
            )
            return redirect(reverse('submission_licenses'))

    elif 'order[]' in request.POST:
        ids = [int(_id) for _id in request.POST.getlist('order[]')]

        for license in licenses:
            order = ids.index(license.pk)
            license.order = order
            license.save()

        return HttpResponse('Thanks')

    template = 'submission/manager/licenses.html'
    context = {
        'license': license_obj,
        'form': form,
        'licenses': licenses,
    }

    return render(request, template, context)


@role_can_access('licenses')
def delete_license(request, license_pk):
    """
    Presents an interface to delete a license object.
    :param request: HttpRequest object
    :param license_pk: int, Licence object pk
    :return: HttpResponse or HttpRedirect
    """
    license_to_delete = get_object_or_404(
        models.Licence,
        pk=license_pk,
        journal=request.journal
    )
    license_articles = models.Article.objects.filter(
        license=license_to_delete
    )

    if request.POST and 'delete' in request.POST:
        messages.add_message(
            request,
            messages.INFO,
            _('License {license_name} deleted.').format(
                license_name=license_to_delete.name,
            ),
        )
        license_to_delete.delete()

        return redirect(reverse('submission_licenses'))

    template = 'submission/manager/delete_license.html'
    context = {
        'license': license_to_delete,
        'license_articles': license_articles,
    }

    return render(request, template, context)


@editor_user_required
def configurator(request):
    """
    Presents an interface for enabling and disabling fixed submission fields.
    :param request: HttpRequest object
    :return: HttpResponse or HttpRedirect
    """
    configuration = request.journal.submissionconfiguration

    form = forms.ConfiguratorForm(instance=configuration)

    if request.POST:
        form = forms.ConfiguratorForm(request.POST, instance=configuration)

        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.INFO,
                _('Configuration updated.'),
            )
            return redirect(reverse('submission_configurator'))

    template = 'submission/manager/configurator.html'
    context = {
        'configuration': configuration,
        'form': form,
    }

    return render(request, template, context)


@method_decorator(login_required, name='dispatch')
class OrganizationListView(GenericFacetedListView):
    """
    Allows a user to search for an organization to add
    as an affiliation of a frozen author record.
    """

    model = core_models.Organization
    template_name = 'admin/core/organization_search.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        article = get_object_or_404(
            models.Article,
            pk=int(self.kwargs.get('article_id')),
            journal=self.request.journal,
        )
        author = get_object_or_404(
            models.FrozenAuthor,
            Q(pk=int(self.kwargs.get('author_id'))) &
            Q(article=article) &
            (Q(author=self.request.user) |
            Q(article__owner=self.request.user))
        )
        context['article'] = article
        context['author'] = author
        return context

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        # Exclude user-created organizations from search results
        return queryset.exclude(custom_label__isnull=False)

    def get_facets(self):
        return {
            'q': {
                'type': 'search',
                'field_label': 'Search',
            },
        }


@login_required
def organization_name_create(request, article_id, author_id):
    """
    Allows a user to create a custom organization name
    if they cannot find one in ROR data.
    """

    next_url = request.GET.get('next', '')
    form = OrganizationNameForm()
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    author = get_object_or_404(
        models.FrozenAuthor,
        Q(pk=author_id) &
        Q(article=article) &
        (Q(author=request.user) |
        Q(article__owner=request.user))
    )

    if request.method == 'POST':
        org_name = create_organization_name(request)
        if org_name:
            return redirect(
                reverse_with_next(
                    'submission_affiliation_create',
                    next_url,
                    kwargs={
                        'article_id': article.pk,
                        'author_id': author.pk,
                        'organization_id': org_name.custom_label_for.pk,
                    }
                )
            )
    context = {
        'article': article,
        'author': author,
        'form': form,
    }
    template = 'admin/core/organizationname_form.html'
    return render(request, template, context)


@login_required
@article_edit_user_required
def organization_name_update(request, article_id, author_id, organization_name_id):
    """
    Allows a user to update a custom organization name
    if it is affiliated with an author they can edit.
    """
    next_url = request.GET.get('next', '')
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    author = get_object_or_404(
        models.FrozenAuthor,
        Q(pk=author_id) &
        Q(article=article) &
        (Q(author=request.user) |
        Q(article__owner=request.user))
    )
    organization_name = get_object_or_404(
        core_models.OrganizationName,
        pk=organization_name_id,
        custom_label_for__controlledaffiliation__frozen_author=author,
    )
    form = OrganizationNameForm(instance=organization_name)

    if request.method == 'POST':
        form = OrganizationNameForm(
            request.POST,
            instance=organization_name,
        )
        if form.is_valid():
            organization = form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Custom organization updated: %(organization)s")
                    % {"organization": organization},
            )
            if next_url:
                return redirect(next_url)
            else:
                return redirect(
                    reverse(
                        'submit_authors',
                        kwargs={'article_id': article_id}
                    )
                )

    template = 'admin/core/organizationname_form.html'
    context = {
        'article': article,
        'author': author,
        'form': form,
    }
    return render(request, template, context)


@login_required
def affiliation_create(request, article_id, author_id, organization_id):
    """
    Allows a user to create a new affiliation
    for an author if they are the owner of the
    author record or the associated account.
    """

    next_url = request.GET.get('next', '')
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    author = get_object_or_404(
        models.FrozenAuthor,
        Q(pk=author_id) &
        Q(article=article) &
        (Q(author=request.user) |
        Q(article__owner=request.user))
    )
    organization = get_object_or_404(
        core_models.Organization,
        pk=organization_id,
    )
    form = forms.AuthorAffiliationForm(
        frozen_author=author,
        organization=organization,
    )

    if request.method == 'POST':
        form = forms.AuthorAffiliationForm(
            request.POST,
            frozen_author=author,
            organization=organization,
        )
        if form.is_valid():
            affiliation = form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Affiliation created: %(affiliation)s")
                    % {"affiliation": affiliation},
            )
            if next_url:
                return redirect(next_url)
            else:
                return redirect(
                    reverse(
                        'submit_authors',
                        kwargs={'article_id': article_id}
                    )
                )

    template = 'admin/core/affiliation_form.html'
    context = {
        'article': article,
        'author': author,
        'form': form,
        'organization': organization,
    }
    return render(request, template, context)


@login_required
@article_edit_user_required
def affiliation_update(request, article_id, author_id, affiliation_id):
    """
    Allows a user to update an affiliation for
    an author they are the author, or if they own the article.
    """
    next_url = request.GET.get('next', '')
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    author = get_object_or_404(
        models.FrozenAuthor,
        Q(pk=author_id) &
        Q(article=article) &
        (Q(author=request.user) |
        Q(article__owner=request.user))
    )
    affiliation = get_object_or_404(
        core_models.ControlledAffiliation,
        pk=affiliation_id,
        frozen_author=author,
    )
    form = forms.AuthorAffiliationForm(
        instance=affiliation,
        frozen_author=author,
        organization=affiliation.organization,
    )

    if request.method == 'POST':
        form = forms.AuthorAffiliationForm(
            request.POST,
            instance=affiliation,
            frozen_author=author,
            organization=affiliation.organization,
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Affiliation updated: %(affiliation)s")
                    % {"affiliation": affiliation},
            )
            if next_url:
                return redirect(next_url)
            else:
                return redirect(
                    reverse(
                        'submit_authors',
                        kwargs={'article_id': article_id}
                    )
                )

    template = 'admin/core/affiliation_form.html'
    context = {
        'article': article,
        'author': author,
        'form': form,
        'affiliation': affiliation,
        'organization': affiliation.organization,
    }
    return render(request, template, context)


@login_required
@article_edit_user_required
def affiliation_delete(request, article_id, author_id, affiliation_id):
    """
    Allows a user to delete an author affiliation
    if they are the author or they own the article.
    """

    next_url = request.GET.get('next', '')
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    author = get_object_or_404(
        models.FrozenAuthor,
        Q(pk=author_id) &
        Q(article=article) &
        (Q(author=request.user) |
        Q(article__owner=request.user))
    )
    affiliation = get_object_or_404(
        core_models.ControlledAffiliation,
        pk=affiliation_id,
        frozen_author=author,
    )
    form = ConfirmDeleteForm()

    if request.method == 'POST':
        form = ConfirmDeleteForm(request.POST)
        if form.is_valid():
            affiliation.delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Affiliation deleted: %(affiliation)s")
                    % {"affiliation": affiliation},
            )
            if next_url:
                return redirect(next_url)
            else:
                return redirect(
                    reverse(
                        'submit_authors',
                        kwargs={'article_id': article_id}
                    )
                )

    template = 'admin/core/affiliation_confirm_delete.html'
    context = {
        'article': article,
        'author': author,
        'form': form,
        'affiliation': affiliation,
        'organization': affiliation.organization,
        'thing_to_delete': str(affiliation),
    }
    return render(request, template, context)


@login_required
@article_edit_user_required
def affiliation_update_from_orcid(
    request,
    article_id,
    author_id,
    how_many='primary',
):
    """
    Allows a user to update the affiliations
    from public ORCID records for an author record they own.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    next_url = request.GET.get('next', '')
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal,
    )
    author = get_object_or_404(
        models.FrozenAuthor,
        pk=author_id,
        article=article,
        article__owner=request.user,
    )
    try:
        cleaned_orcid = clean_orcid_id(author.orcid)
    except ValueError:
        cleaned_orcid = None
    if not cleaned_orcid:
        messages.add_message(
            request,
            messages.WARNING,
            _("%(author_name)s (%(email)s) does not have an ORCID. Please re-add them "
              "by searching for their ORCID and try again.")
                % {
                    "author_name": author.full_name(),
                    "email": author.email
                },
            )
        if next_url:
            return redirect(next_url)
        else:
            return redirect(
                reverse(
                    'submit_authors',
                    kwargs={'article_id': article_id}
                )
            )

    orcid_details = orcid.get_orcid_record_details(cleaned_orcid)
    orcid_affils = orcid_details.get("affiliations", [])
    if not orcid_affils:
        messages.add_message(
            request,
            messages.WARNING,
            _("No affiliations were found on your public ORCID record "
              "for ID %(orcid_id)s. "
              "Please update your affiliations on orcid.org and try again.")
                % {'orcid_id': request.user.orcid },
        )
        if next_url:
            return redirect(next_url)
        else:
            return redirect(
                reverse(
                    'submit_authors',
                    kwargs={'article_id': article_id}
                )
            )

    form = ConfirmDeleteForm()
    new_affils = []
    if how_many == 'primary':
        orcid_affils = orcid_affils[:1]
    for orcid_affil in orcid_affils:
        orcid_affil_form = OrcidAffiliationForm(
            orcid_affil,
            tzinfo=request.user.preferred_timezone,
            data={"frozen_author": author},
        )
        if orcid_affil_form.is_valid():
            new_affils.append(orcid_affil_form.save(commit=False))

    if request.method == 'POST':
        form = ConfirmDeleteForm(request.POST)
        if form.is_valid():
            author.affiliations.delete()
            for affil in new_affils:
                affil.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Affiliations updated."),
            )
            if next_url:
                return redirect(next_url)
            else:
                return redirect(
                    reverse(
                        'submit_authors',
                        kwargs={'article_id': article_id}
                    )
                )

    template = "admin/core/affiliation_update_from_orcid.html"
    context = {
        'article': article,
        'author': author,
        'form': form,
        'old_affils': author.affiliations,
        'new_affils': new_affils,
    }
    return render(request, template, context)

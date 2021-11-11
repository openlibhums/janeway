__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone, translation
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from core import files, models as core_models
from preprint import models as preprint_models
from security.decorators import (
    article_edit_user_required,
    production_user_or_editor_required,
    editor_user_required,
)
from submission import forms, models, logic, decorators
from events import logic as event_logic
from utils import setting_handler
from utils import shared as utils_shared
from utils.decorators import GET_language_override
from utils.shared import create_language_override_redirect


@login_required
@decorators.submission_is_enabled
def start(request, type=None):
    """
    Starts the submission process, presents various checkboxes and then creates a new article.
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

            if setting_handler.get_setting(
                    'general',
                    'user_automatically_author',
                    request.journal,
            ).processed_value:
                logic.add_user_as_author(request.user, new_article)

            return redirect(reverse('submit_info', kwargs={'article_id': new_article.pk}))

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
@article_edit_user_required
def submit_funding(request, article_id):
    """
    Presents a form for the user to complete with article information
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(models.Article, pk=article_id)
    additional_fields = models.Field.objects.filter(journal=request.journal)
    submission_summary = setting_handler.get_setting(
        'general',
        'submission_summary',
        request.journal,
    ).processed_value
    form = forms.ArticleInfoSubmit(
        instance=article,
        additional_fields=additional_fields,
        submission_summary=submission_summary,
        journal=request.journal,
    )

    if request.POST:
        if 'next_step' in request.POST:
            article.current_step = 5
            article.save()
            return redirect(reverse('submit_review', kwargs={'article_id': article_id}))

        funder = models.Funder(
            name=request.POST.get('funder_name', default=''),
            fundref_id=request.POST.get('funder_doi', default=''),
            funding_id=request.POST.get('grant_number', default=''),
        )

        funder.save()
        article.funders.add(funder)
        article.save()

    template = 'admin/submission//submit_funding.html'
    context = {
        'article': article,
        'form': form,
        'additional_fields': additional_fields,
    }

    return render(request, template, context)


@login_required
@decorators.submission_is_enabled
@article_edit_user_required
def submit_info(request, article_id):
    """
    Presents a form for the user to complete with article information
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse or HttpRedirect
    """
    with translation.override(settings.LANGUAGE_CODE):
        article = get_object_or_404(models.Article, pk=article_id)
        additional_fields = models.Field.objects.filter(journal=request.journal)
        submission_summary = setting_handler.get_setting(
            'general',
            'submission_summary',
            request.journal,
        ).processed_value
        form = forms.ArticleInfoSubmit(
            instance=article,
            additional_fields=additional_fields,
            submission_summary=submission_summary,
            journal=request.journal,
        )

        if request.POST:
            form = forms.ArticleInfoSubmit(
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

        article = models.Article.objects.get(pk=article_id)

        for he in article.publisher_notes.all():
            he.sequence = ids.index(he.pk)
            he.save()

    return HttpResponse('Thanks')


@login_required
@decorators.submission_is_enabled
@article_edit_user_required
def submit_authors(request, article_id):
    """
    Allows the submitting author to add other authors to the submission.
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpRedirect or HttpResponse
    """
    article = get_object_or_404(models.Article, pk=article_id)

    if article.current_step < 2 and not request.user.is_staff:
        return redirect(reverse('submit_info', kwargs={'article_id': article_id}))

    form = forms.AuthorForm()
    error, modal = None, None

    if request.GET.get('add_self', None) == 'True':
        new_author = logic.add_user_as_author(request.user, article)
        messages.add_message(
            request,
            messages.SUCCESS,
            _('{author_name} added to the article.').format(
                author_name=new_author.full_name(),
            ),
        )
        return redirect(
            reverse(
                'submit_authors',
                kwargs={'article_id': article_id},
            )
        )

    if request.POST and 'add_author' in request.POST:
        form = forms.AuthorForm(request.POST)
        modal = 'author'

        email = request.POST.get("email")
        author = None
        author_exists = logic.check_author_exists(email=email)
        if author_exists:
            author = core_models.Account.objects.get(email=email)
        elif form.is_valid():
            new_author = form.save(commit=False)
            new_author.set_password(utils_shared.generate_password())
            new_author.save()
            author = new_author
        else:
            messages.add_message(
                request, messages.WARNING,
                _('Errors found in the new author form'),
            )

        if author:
            logic.add_user_as_author(author, article)
            messages.add_message(
                request, messages.SUCCESS,
                _('{author_name} added to the article.').format(
                    author_name=author.full_name(),
                ),
            )
            return redirect(reverse(
                'submit_authors', kwargs={'article_id': article_id}))

    elif request.POST and 'search_authors' in request.POST:
        search = request.POST.get('author_search_text', None)

        if not search:
            messages.add_message(
                request,
                messages.WARNING,
                _('An empty search is not allowed.'),
            )
        else:
            try:
                search_author = core_models.Account.objects.get(
                    Q(email=search) | Q(orcid=search)
                )
                logic.add_user_as_author(search_author, article)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _('{author_name} added to the article.').format(
                        author_name=search_author.full_name(),
                    ),
                )
            except core_models.Account.DoesNotExist:
                messages.add_message(
                    request, messages.WARNING,
                    _('No author found with those details.'),
                )

    elif request.POST and 'main-author' in request.POST:
        correspondence_author = request.POST.get('main-author', None)

        if correspondence_author == 'None':
            messages.add_message(
                request,
                messages.WARNING,
                _('You must select a main author.'),
            )
        else:
            author = core_models.Account.objects.get(pk=correspondence_author)
            article.correspondence_author = author
            article.current_step = 3
            article.save()

            return redirect(reverse(
                'submit_files', kwargs={'article_id': article_id}))

    elif request.POST and 'authors[]' in request.POST:
        logic.save_author_order(request, article)

        return HttpResponse('Complete')

    template = 'admin/submission//submit_authors.html'
    context = {
        'error': error,
        'article': article,
        'form': form,
        'modal': modal,
    }

    return render(request, template, context)


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
    funding = get_object_or_404(
        models.Funder,
        pk=funder_id
    )

    article.funders.remove(funding)

    if request.GET.get('return'):
        return redirect(request.GET['return'])

    return redirect(reverse('submit_funding', kwargs={'article_id': article_id}))



@login_required
@article_edit_user_required
def delete_author(request, article_id, author_id):
    """Allows submitting author to delete an author object."""
    article = get_object_or_404(
        models.Article,
        pk=article_id,
        journal=request.journal
    )
    author = get_object_or_404(
        core_models.Account,
        pk=author_id
    )

    article.authors.remove(author)

    if article.correspondence_author == author:
        article.correspondence_author = None

    try:
        ordering = models.ArticleAuthorOrder.objects.get(
            article=article,
            author=author,
        ).delete()
    except models.ArticleAuthorOrder.DoesNotExist:
        pass

    return redirect(reverse('submit_authors', kwargs={'article_id': article_id}))


@login_required
@decorators.submission_is_enabled
@article_edit_user_required
def submit_files(request, article_id):
    """
    Allows the submitting author to upload files and links them to the submission
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse
    """
    article = get_object_or_404(models.Article, pk=article_id)
    form = forms.FileDetails()
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
            form = forms.FileDetails(request.POST)
            uploaded_file = request.FILES.get('file')
            if logic.check_file(uploaded_file, request, form):
                if form.is_valid():
                    new_file = files.save_file_to_article(
                        uploaded_file,
                        article,
                        request.user,
                    )
                    article.manuscript_files.add(new_file)
                    new_file.label = form.cleaned_data['label']
                    new_file.description = form.cleaned_data['description']
                    new_file.save()
                    return redirect(
                        reverse('submit_files', kwargs={'article_id': article_id}),
                    )
                else:
                    modal = 'manuscript'
            else:
                modal = 'manuscript'

        if 'data' in request.POST:
            for uploaded_file in request.FILES.getlist('file'):
                form = forms.FileDetails(request.POST)
                if form.is_valid():
                    new_file = files.save_file_to_article(
                        uploaded_file,
                        article,
                        request.user,
                    )
                    article.data_figure_files.add(new_file)
                    new_file.label = form.cleaned_data['label']
                    new_file.description = form.cleaned_data['description']
                    new_file.save()
                    return redirect(reverse('submit_files', kwargs={'article_id': article_id}))
                else:
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
                error = "You must upload a manuscript file."

    template = "admin/submission//submit_files.html"
    context = {
        'article': article,
        'error': error,
        'form': form,
        'modal': modal,
    }

    return render(request, template, context)


@login_required
@decorators.submission_is_enabled
@article_edit_user_required
def submit_review(request, article_id):
    """
    A page that allows the user to review a submission.
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(models.Article, pk=article_id)

    if article.current_step < 4 and not request.user.is_staff:
        return redirect(
            reverse(
                'submit_info',
                kwargs={'article_id': article_id},
            )
        )

    if request.POST and 'next_step' in request.POST:
        article.date_submitted = timezone.now()
        article.stage = models.STAGE_UNASSIGNED
        article.current_step = 5
        article.snapshot_authors(article)
        article.save()

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

        event_logic.Events.raise_event(
            event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE,
            **{'handshake_url': 'submit_review',
               'request': request,
               'article': article,
               'switch_stage': False}
        )

        return redirect(reverse('core_dashboard'))

    template = "admin/submission//submit_review.html"
    context = {
        'article': article,
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
        article = get_object_or_404(models.Article, pk=article_id)
        submission_summary = setting_handler.get_setting(
            'general',
            'submission_summary',
            request.journal,
        ).processed_value
        info_form = forms.ArticleInfo(
            instance=article,
            submission_summary=submission_summary,
            pop_disabled_fields=False,
        )
        frozen_author, modal = None, None
        return_param = request.GET.get('return')
        reverse_url = create_language_override_redirect(
            request,
            'edit_metadata',
            {'article_id': article.pk},
            query_strings={'return': return_param}
        )

        if request.GET.get('author'):
            frozen_author, modal = logic.get_author(request, article)
            author_form = forms.EditFrozenAuthor(instance=frozen_author)
        else:
            author_form = forms.EditFrozenAuthor()

        if request.POST:
            if 'add_funder' in request.POST:
                funder = models.Funder(
                    name=request.POST.get('funder_name', default=''),
                    fundref_id=request.POST.get('funder_doi', default=''),
                    funding_id=request.POST.get('grant_number', default='')
                )

                funder.save()
                article.funders.add(funder)
                article.save()

            if 'metadata' in request.POST:
                info_form = forms.ArticleInfo(
                    request.POST,
                    instance=article,
                    submission_summary=submission_summary,
                    pop_disabled_fields=False,
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
                    _('Primary author set.')
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
        'info_form': info_form,
        'author_form': author_form,
        'modal': modal,
        'frozen_author': frozen_author,
        'return': return_param
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


@editor_user_required
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


@staff_member_required
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

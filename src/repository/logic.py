from dateutil.relativedelta import relativedelta
from user_agents import parse as parse_ua_string
from datetime import timedelta
from collections import Counter

from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import (
    CharField,
    Q,
    OuterRef,
    Subquery,
    Value,
)
from django.db.models.functions import Concat
from django.forms import formset_factory

from production.logic import save_galley
from core import models as core_models, files
from utils import render_template, shared
from utils.function_cache import cache
from events import logic as event_logic
from repository import models, forms
from metrics.logic import get_iso_country_code, iso_to_country_object


def get_month_day_range(date):
    """
    For a date 'date' returns the start and end date for the month of 'date'.
    """
    last_day = date + relativedelta(day=1, months=+1, days=-1)
    first_day = date + relativedelta(day=1)
    return first_day, last_day


def metrics_summary(published_preprints):
    """
    Fetches view counts for a month and year.
    :param published_preprints: preprint queryset
    :return: dictionary with access results
    """
    first_this_month, last_this_month = get_month_day_range(timezone.now())
    last_month_date = timezone.now() - relativedelta(months=1)
    first_last_month, last_last_month = get_month_day_range(last_month_date)

    total_accesses_this_month = models.PreprintAccess.objects.filter(
        accessed__gte=first_this_month,
        accessed__lte=last_this_month,
        preprint__in=published_preprints,
    )

    total_accesses_last_month = models.PreprintAccess.objects.filter(
        accessed__gte=first_last_month,
        accessed__lte=last_last_month,
        preprint__in=published_preprints,
    )

    views_this_month = total_accesses_this_month.filter(
        file__isnull=True,
    ).count()
    views_last_month = total_accesses_last_month.filter(
        file__isnull=True,
    ).count()
    downloads_this_month = total_accesses_this_month.filter(
        file__isnull=False,
    ).count()
    downloads_last_monnth = total_accesses_last_month.filter(
        file__isnull=False,
    ).count()


    return {
        'views_this_month': views_this_month,
        'views_last_month': views_last_month,
        'downloads_this_month': downloads_this_month,
        'downloads_last_monnth': downloads_last_monnth,
    }


def handle_file_upload(request, preprint):
    if 'file' in request.FILES:
        label = request.POST.get('label')
        for uploaded_file in request.FILES.getlist('file'):
            save_galley(
                preprint,
                request,
                uploaded_file,
                True,
                label=label,
            )


def determine_action(preprint):
    if preprint.date_accepted and not preprint.date_declined:
        return 'accept'
    else:
        return 'decline'


def get_pdf(article):
    try:
        try:
            pdf = article.galley_set.get(file__mime_type='application/pdf')
        except core_models.Galley.MultipleObjectsReturned:
            pdf = article.galley_set.filter(file__mime_type='application/pdf')[0]
    except core_models.Galley.DoesNotExist:
        pdf = None

    return pdf


def get_html(article):
    try:
        galley = article.galley_set.get(type='html')
        html = galley.file_content()
    except core_models.Galley.DoesNotExist:
        html = None

    return html


def get_publication_text(request, preprint, action):
    context = {
        'preprint': preprint,
        'request': request,
        'action': action,
    }

    if preprint.date_declined and not preprint.date_published:
        template = request.repository.decline
    else:
        template = request.repository.publication
    email_content = render_template.get_message_content(
        request,
        context,
        template,
        template_is_setting=True,
    )
    return email_content


def raise_comment_event(request, comment):
    kwargs = {
        'request': request,
        'preprint': comment.preprint,
        'comment': comment,
    }
    event_logic.Events.raise_event(
        event_logic.Events.ON_PREPRINT_COMMENT,
        **kwargs,
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        'Your comment has been saved. It has been sent for moderation.',
    )


def comment_manager_post(request, preprint):
    if 'comment_public' in request.POST:
        comment_id = request.POST.get('comment_public')
    else:
        comment_id = request.POST.get('comment_reviewed')

    comment = get_object_or_404(
        models.Comment,
        pk=comment_id,preprint=preprint,
    )

    if 'comment_public' in request.POST:
        comment.toggle_public()

    else:
        comment.mark_reviewed()


# TODO: Update this implementation
def handle_author_post(request, preprint):
    file = request.FILES.get('file')
    update_type = request.POST.get('upload_type')
    galley_id = request.POST.get('galley_id')
    galley = get_object_or_404(core_models.Galley, article=preprint, pk=galley_id)

    if request.press.preprint_pdf_only and not files.check_in_memory_mime(in_memory_file=file) == 'application/pdf':
        messages.add_message(request, messages.WARNING, 'You must upload a PDF file.')
        return
    else:
        file = files.save_file_to_article(file, preprint, request.user, label=galley.label)

    models.VersionQueue.objects.create(article=preprint, galley=galley, file=file, update_type=update_type)

    messages.add_message(request, messages.INFO, 'This update has been added to the moderation queue.')


# TODO: Update this implementation
def get_pending_update_from_post(request):
    """
    Gets a VersionQueue object from a post value
    :param request: HttpRequest object
    :return: VersionQueue object or None
    """
    update_id = None

    if 'approve' in request.POST:
        update_id = request.POST.get('approve')
    elif 'decline' in request.POST:
        update_id = request.POST.get('decline')

    if update_id:
        pending_update = get_object_or_404(
            models.VersionQueue,
            pk=update_id,
            date_decision__isnull=True,
            preprint__repository=request.repository,
        )
        return pending_update
    else:
        return None


# TODO: Update this implementation
def approve_pending_update(request):
    """
    Approves a pending versioning request and updates files/galleys.
    :param request: HttpRequest object
    :return: None
    """
    pending_update = get_pending_update_from_post(request)

    if pending_update:
        pending_update.approve()
        messages.add_message(
            request,
            messages.INFO,
            'New version created.',
        )
        kwargs = {
            'pending_update': pending_update,
            'request': request,
            'action': 'accept',
        }
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_VERSION_UPDATE,
            **kwargs,
        )
    else:
        messages.add_message(
            request,
            messages.WARNING,
            'No valid pending update found.',
        )

    return redirect(reverse('version_queue'))


def decline_pending_update(request):
    pending_update = get_pending_update_from_post(request)

    if pending_update:
        pending_update.decline()
        messages.add_message(
            request,
            messages.INFO,
            'New version declined.',
        )
        kwargs = {
            'pending_update': pending_update,
            'request': request,
            'action': 'decline',
            'reason': request.POST.get('reason', 'No reason supplied.')
        }
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_VERSION_UPDATE,
            **kwargs,
        )
    else:
        messages.add_message(
            request,
            messages.WARNING,
            'No valid pending update found.',
        )
    return redirect(reverse('version_queue'))


def handle_delete_version(request, preprint):
    version_id = request.POST.get('delete_version')

    if not version_id:
        messages.add_message(
            request,
            messages.WARNING,
            'No version id supplied')
    else:
        version = get_object_or_404(
            models.PreprintVersion,
            pk=version_id,
            preprint=preprint,
        )
        version.delete()
        messages.add_message(
            request,
            messages.INFO,
            'Version deleted.',
        )


def delete_file(request, preprint):
    """
    Fetches the file to be deleted, checks that it belongs to a preprint
    and deletes it.
    :param request: HttpRequest object
    :param preprint: Preprint object
    :return: None
    """
    file_id = request.POST.get('delete_file')

    if not file_id:
        messages.add_message(
            request,
            messages.WARNING,
            'No File ID supplied.'
        )
    try:
        models.PreprintFile.objects.get(
            pk=file_id,
            preprint=preprint,
        ).delete()
    except models.PreprintFile.DoesNotExist:
        messages.add_message(
            request,
            messages.WARNING,
            'No matching File found.'
        )


def subject_article_pks(user):
    prepint_pks = []
    for subject in user.preprint_subjects():
        for preprint in subject.preprint_set.all():
            prepint_pks.append(preprint.pk)

    return prepint_pks


def get_unpublished_preprints(request, user_subject_pks):
    author_name_subq = models.PreprintAuthor.objects.filter(
        preprint=OuterRef('pk')
    ).annotate(
        full_name=Concat(
            "account__first_name", Value(" "), "account__last_name",
            output_field=CharField(),
        )
    ).values('full_name')
    unpublished_preprints = models.Preprint.objects.filter(
        date_published__isnull=True,
        date_submitted__isnull=False,
        date_declined__isnull=True,
        date_accepted__isnull=True,
        repository=request.repository,
    ).annotate(
        author_full_name=Subquery(author_name_subq[:1])
    )

    if request.user.is_staff or request.user.is_repository_manager(request.repository):
        return unpublished_preprints
    else:
        return unpublished_preprints.filter(pk__in=user_subject_pks)


def get_published_preprints(request, user_subject_pks):
    author_name_subq = models.PreprintAuthor.objects.filter(
        preprint=OuterRef('pk')
    ).annotate(
        full_name=Concat(
            "account__first_name", Value(" "), "account__last_name",
            output_field=CharField(),
        )
    ).values('full_name')
    published_preprints = models.Preprint.objects.filter(
        date_published__isnull=False,
        date_submitted__isnull=False,
        repository=request.repository,
    ).annotate(
        author_full_name=Subquery(author_name_subq[:1])
    )

    if request.user.is_staff or request.user.is_repository_manager(request.repository):
        return published_preprints
    else:
        return published_preprints.filter(pk__in=user_subject_pks)


@cache(300)
def list_articles_without_subjects(repository=None):
    preprints = models.Preprint.objects.filter(
        date_submitted__isnull=False,
        subject__isnull=True,
    )
    if repository:
        preprints = preprints.filter(
            repository=repository,
        )
    return preprints


def get_doi(request, preprint):
    """
    Returns either the articles actual DOI or a rendered one using the press' pattern.
    :param request: HttpRequest object
    :param preprint: Preprint object
    :return:
    """
    doi = preprint.get_doi()

    if doi:
        return doi

    else:
        doi = render_template.get_message_content(
            request,
            {'preprint': preprint},
            request.press.get_setting_value('Crossref Pattern'),
            template_is_setting=True,
        )
        return doi


def get_list_of_preprint_journals():
    """
    Returns a list of journals who allow preprints to be submitted to them.
    :return: Queryset of Journal objects
    """
    from journal import models as journal_models
    journals = journal_models.Journal.objects.all()
    journals_accepting_preprints = list()

    for journal in journals:
        setting = journal.get_setting(
            'general',
            'accepts_preprint_submissions',
        )
        if setting:
            journals_accepting_preprints.append(journal)

    return journals_accepting_preprints


def check_duplicates(version_queue):
    preprints = [version_request.preprint for version_request in version_queue]
    return [k for k,v in Counter(preprints).items() if v > 1]


def search_for_authors(request, preprint):
    search_term = request.POST.get('search')
    try:
        search_author = core_models.Account.objects.get(
            Q(email=search_term) | Q(orcid=search_term)
        )
        pa, created = models.PreprintAuthor.objects.get_or_create(
            account=search_author,
            preprint=preprint,
            defaults={'order': preprint.next_author_order()},
        )

        if not created:
            messages.add_message(
                request,
                messages.WARNING,
                'This author is already associated with this {}'.format(
                    request.repository.object_name,
                )
            )

        return pa
    except core_models.Account.DoesNotExist:
        messages.add_message(
            request,
            messages.INFO,
            'No author found.'
        )


def raise_event(event_type, request, preprint):
    kwargs = {
        'request': request,
        'preprint': preprint,
    }

    if event_type == 'accept':
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_PUBLICATION,
            **kwargs,
        )


def store_preprint_access(request, preprint, file=None):
    try:
        user_agent = parse_ua_string(request.META.get('HTTP_USER_AGENT', None))
    except TypeError:
        user_agent = None

    if user_agent and not user_agent.is_bot:

        ip = shared.get_ip_address(request)
        iso_country_code = get_iso_country_code(ip)
        country = iso_to_country_object(iso_country_code)
        counter_tracking_id = request.session.get('counter_tracking')
        identifier = counter_tracking_id if counter_tracking_id else hash(ip)

        # Check if someone with this identifier has accessed the same file
        # within the last X seconds
        time_to_check = timezone.now() - timedelta(seconds=30)

        if not models.PreprintAccess.objects.filter(
            preprint=preprint,
            file=file,
            identifier=identifier,
            accessed__gte=time_to_check,
        ).exists():

            models.PreprintAccess.objects.create(
                preprint=preprint,
                file=file,
                identifier=identifier,
                country=country,
            )


def get_review_notification(request, preprint, review):
    url = request.repository.site_url(
        path=reverse(
            'repository_submit_review',
            kwargs={
                'review_id': review.pk,
                'access_code': review.access_code,
            }
        )
    )
    context = {
        'preprint': preprint,
        'request': request,
        'review': review,
        'url': url,
    }
    template = request.repository.review_invitation
    email_content = render_template.get_message_content(
        request,
        context,
        template,
        template_is_setting=True,
    )
    return email_content

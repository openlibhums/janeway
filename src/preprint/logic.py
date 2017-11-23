from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages

from metrics import models as metrics_models
from production.logic import save_galley
from core import models as core_models, files
from utils import render_template
from utils.function_cache import cache
from events import logic as event_logic
from preprint import models
from submission import models as submission_models


def get_display_modal(request):
    """
    Determins which file modal should be displayed when there is a form error.
    :param request: HttpRequest
    :return: string
    """
    if 'manuscript' in request.POST:
        return 'manuscript'
    elif 'data' in request.POST:
        return 'data'


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
    :param month: month
    :param year: year
    :return: view count, integer
    """
    first_this_month, last_this_month = get_month_day_range(timezone.now())

    last_month_date = timezone.now() - relativedelta(months=1)
    first_last_month, last_last_month = get_month_day_range(last_month_date)

    views = metrics_models.ArticleAccess.objects.filter(accessed__gte=first_this_month,
                                                        accessed__lte=last_this_month,
                                                        article__in=published_preprints,
                                                        type='view').count()

    downloads = metrics_models.ArticleAccess.objects.filter(accessed__gte=first_this_month,
                                                            accessed__lte=last_this_month,
                                                            article__in=published_preprints,
                                                            type='download').count()

    last_views = metrics_models.ArticleAccess.objects.filter(accessed__gte=first_last_month,
                                                             accessed__lte=last_last_month,
                                                             article__in=published_preprints,
                                                             type='view').count()

    last_downloads = metrics_models.ArticleAccess.objects.filter(accessed__gte=first_last_month,
                                                                 accessed__lte=last_last_month,
                                                                 article__in=published_preprints,
                                                                 type='download').count()

    return {'views': views, 'downloads': downloads,
            'last_views': last_views, 'last_downloads': last_downloads}


def handle_file_upload(request, preprint):
    if 'xml' in request.POST:
        for uploaded_file in request.FILES.getlist('xml-file'):
            new_galley = save_galley(preprint, request, uploaded_file, True, "XML", False)

    if 'pdf' in request.POST:
        for uploaded_file in request.FILES.getlist('pdf-file'):
            new_galley = save_galley(preprint, request, uploaded_file, True, "PDF", False)

    if 'other' in request.POST:
        for uploaded_file in request.FILES.getlist('other-file'):
            new_galley = save_galley(preprint, request, uploaded_file, True, "Other", True)


def determie_action(preprint):
    if preprint.date_accepted and not preprint.date_declined:
        return 'accept'
    else:
        return 'decline'


def get_pdf(article):
    try:
        pdf = article.galley_set.get(type='pdf')
    except core_models.Galley.DoesNotExist:
        try:
            pdf = article.galley_set.get(file__mime_type='application/pdf')
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


def get_publication_text(request, article, action):
    context = {
        'article': article,
        'request': request,
        'action': action,
    }

    template = request.press.preprint_publication
    email_content = render_template.get_message_content(request, context, template, template_is_setting=True)
    return email_content


def handle_comment_post(request, article, comment):
    comment.article = article
    comment.author = request.user
    comment.save()

    kwargs = {'request': request, 'article': article, 'comment': comment}
    event_logic.Events.raise_event(event_logic.Events.ON_PREPRINT_COMMENT, **kwargs)

    messages.add_message(request, messages.SUCCESS, 'Your comment has been saved. It has been sent for moderation.')


def comment_manager_post(request, preprint):
    if 'comment_public' in request.POST:
        comment_id = request.POST.get('comment_public')
    else:
        comment_id = request.POST.get('comment_reviewed')

    comment = get_object_or_404(models.Comment, pk=comment_id, article=preprint)

    if 'comment_public' in request.POST:
        if comment.is_public:
            comment.is_public = False
        else:
            comment.is_public = True

        comment.is_reviewed = True
    else:
        comment.is_reviewed = True

    comment.save()


def handle_author_post(request, preprint):

    file = request.FILES.get('file')
    upload_type = request.POST.get('upload_type')
    galley_id = request.POST.get('galley_id')
    galley = get_object_or_404(core_models.Galley, article=preprint, pk=galley_id)

    if file:
        if upload_type == 'minor_correction':
            galley.file.unlink_file()
            files.overwrite_file(file, preprint, galley.file)
            messages.add_message(request, messages.SUCCESS, 'Existing file replaced.')
        elif upload_type == 'new_version':
            models.PreprintVersion.objects.create(
                preprint=preprint,
                galley=galley,
                version=preprint.next_preprint_version()
            )
            galley.article = None
            galley.save()

            new_galley = save_galley(preprint, request, file, True, galley.type, False)
            new_galley.label = galley.label
            new_galley.save()
            messages.add_message(request, messages.SUCCESS, 'New version created.')

        else:
            messages.add_message(request, messages.ERROR, 'Invalid upload type provided.')
    else:
        messages.add_message(request, messages.ERROR, 'No file uploaded')


def handle_delete_version(request, preprint):
    version_id = request.POST.get('delete')

    if not version_id:
        messages.add_message(request, messages.WARNING, 'No version id supplied')
    else:
        version = get_object_or_404(models.PreprintVersion, pk=version_id, preprint=preprint)
        version.delete()
        messages.add_message(request, messages.INFO, 'Version deleted.')


def handle_delete_subject(request):
    subject_id = request.POST.get('delete')

    subject = get_object_or_404(models.Subject, pk=subject_id)
    messages.add_message(request, messages.INFO, 'Subject "{subject}" deleted.'.format(subject=subject.name))
    subject.delete()
    return redirect(reverse('preprints_subjects'))


def get_subject_articles(subject):
    subject_article_pks = [article.pk for article in subject.preprints.all()]
    return submission_models.Article.preprints.filter(pk__in=subject_article_pks,
                                                      date_published__lte=timezone.now())


def handle_updating_subject(request, preprint):
    """
    Pulls a subject pk from POST, checks it exists and assigns the article to the subject.
    :param request: HttpRequest
    :param preprint: Preprint Object
    :return: Function does not return anything
    """

    subject_pk = request.POST.get('subject')

    if not subject_pk:
        messages.add_message(request, messages.WARNING, 'No subject selected')
    else:
        subject = get_object_or_404(models.Subject, pk=subject_pk, enabled=True)
        preprint.set_preprint_subject(subject)
        messages.add_message(request, messages.INFO, ('Subject Area updated.'))


def subject_article_pks(request):
    article_pks = []
    for subject in request.user.preprint_subjects():
        for article in subject.preprints.all():
            article_pks.append(article.pk)

    return article_pks


def get_unpublished_preprints(request):

    unpublished_preprints = submission_models.Article.preprints.filter(
        date_published__isnull=True,
        date_submitted__isnull=False,
        date_declined__isnull=True,
        date_accepted__isnull=True,
    ).prefetch_related(
        'articleauthororder_set'
    )

    if request.user.is_staff:
        return unpublished_preprints
    else:
        return unpublished_preprints.filter(pk__in=subject_article_pks(request))


def get_published_preprints(request):
    published_preprints = submission_models.Article.preprints.filter(
        date_published__isnull=False,
        date_submitted__isnull=False).prefetch_related(
        'articleauthororder_set'
    )

    if request.user.is_staff:
        return published_preprints
    else:
        return published_preprints.filter(pk__in=subject_article_pks(request))


def unpublish_preprint(request, preprint):
    "Marks a preprint as unpublished."
    preprint.date_accepted = None
    preprint.date_declined = None
    preprint.date_published = None
    preprint.preprint_decision_notification = False
    preprint.stage = submission_models.STAGE_PREPRINT_REVIEW
    preprint.save()
    messages.add_message(request, messages.INFO, 'This preprint has been unpublished')


def get_preprint_article_if_id(request, article_id):
    if article_id:
        article = get_object_or_404(submission_models.Article.preprints,
                                    pk=article_id,
                                    date_submitted__isnull=True)
    else:
        article = None

    return article


def save_preprint_submit_form(request, form, article, additional_fields):
    article = form.save(request=request)
    article.owner = request.user
    article.is_preprint = True
    article.current_step = 1
    article.authors.add(request.user)
    article.correspondence_author = request.user
    article.save()

    submission_models.ArticleAuthorOrder.objects.get_or_create(article=article,
                                                               author=request.user,
                                                               defaults={'order': article.next_author_sort()})
    return article


@cache(300)
def list_articles_without_subjects():
    articles = submission_models.Article.preprints.all()
    subjects =  models.Subject.objects.all()

    subject_articles = list()
    for subject in subjects:
        subject_articles.append(subject.preprints.all())

    subject_articles = set(subject_articles)

    orphaned_articles = list()

    for article in articles:
        if article not in subject_articles:
            orphaned_articles.append(article)

    return orphaned_articles


from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.shortcuts import get_object_or_404

from metrics import models as metrics_models
from production.logic import save_galley
from core import models as core_models
from utils import render_template
from events import logic as event_logic
from preprint import models


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


def comment_manager_post(request, preprint):
    print(request.POST)
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
        print(comment.is_public)
    else:
        comment.is_reviewed = True

    comment.save()
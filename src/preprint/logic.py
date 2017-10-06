from dateutil.relativedelta import relativedelta
import calendar

from django.utils import timezone

from metrics import models as metrics_models


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

    print(published_preprints)

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

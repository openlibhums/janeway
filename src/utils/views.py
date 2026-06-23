__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse

from utils import logic


@csrf_exempt
@require_POST
def mailgun_webhook(request):
    """
    Displays a list of reports.
    :param request: HttpRequest object
    :return: HttpResponse
    """

    message = logic.parse_mailgun_webhook(request.POST)
    return HttpResponse(message)

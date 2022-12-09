__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from cron import models
from django.conf import settings

from utils.middleware import BaseMiddleware


class CronMiddleware(BaseMiddleware):

    @staticmethod
    def process_request(request):
        """ This middleware class calls the Cron runner to process scheduled tasks (like emails)

        :param request: the current request
        :return: None
        """
        if not settings.DEBUG:
            try:
                models.CronTask.run_tasks()
            except BaseException:
                pass
        else:
            models.CronTask.run_tasks()

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from cron import models
from core import settings


class CronMiddleware(object):

    @staticmethod
    def process_request(request):
        """ This middleware class calls the Cron runner to process scheduled tasks (like emails)

        :param request: the current request
        :return: None or an http 404 error in the event of catastrophic failure
        """
        if not settings.DEBUG:
            try:
                models.CronTask.run_tasks()
            except BaseException:
                pass
        else:
            models.CronTask.run_tasks()

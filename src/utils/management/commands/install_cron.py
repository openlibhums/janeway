import os

from django.core.management.base import BaseCommand
from django.conf import settings

from crontab import CronTab


def find_job(tab, comment):
    for job in tab:
        if job.comment == comment:
            return job
    return None


class Command(BaseCommand):
    """
    Installs a cron tasks.
    """

    help = "Installs a cron tasks."

    def add_arguments(self, parser):
        parser.add_argument('--action', default="")

    def handle(self, *args, **options):
        """Installs Cron

        :param args: None
        :param options: None
        :return: None
        """
        action = options.get('action')
        tab = CronTab(user=True)
        virtualenv = os.environ.get('VIRTUAL_ENV', None)

        current_job = find_job(tab, "janeway_cron_job")

        if not current_job:
            django_command = "{0}/manage.py execute_cron_tasks".format(settings.BASE_DIR)
            if virtualenv:
                command = '%s/bin/python3 %s' % (virtualenv, django_command)
            else:
                command = '%s' % (django_command)

            cron_job = tab.new(command, comment="janeway_cron_job")
            cron_job.minute.every(10)

        else:
            print("This cron job already exists.")

        if action == 'test':
            print(tab.render())
        elif action == 'quiet':
            pass
        else:
            tab.write()

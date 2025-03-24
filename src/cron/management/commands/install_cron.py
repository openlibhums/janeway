import os

from django.core.management.base import BaseCommand
from django.conf import settings

try:
    import crontab
except (ImportError, ModuleNotFoundError):
    crontab = None


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
        if not os.path.isfile('/usr/bin/crontab'):
            print("WARNING: /usr/bin/crontab not found, skipping crontab config.")
            return

        if not crontab:
            print("WARNING: crontab module is not installed, skipping crontab config.")
            return

        action = options.get('action')
        tab = crontab.CronTab(user=True)
        virtualenv = os.environ.get('VIRTUAL_ENV', None)

        cwd = settings.PROJECT_DIR.replace('/', '_')

        jobs = [
            {
                'name': '{}_janeway_cron_job'.format(cwd),
                'time': 30,
                'task': 'execute_cron_tasks',
                'type': 'mins',
            },
            {
                'name': '{}_janeway_ithenticate_job'.format(cwd),
                'time': 30,
                'task': 'store_ithenticate_scores',
                'type': 'mins',
            },
            {
                'name': '{}_janeway_sitemaps_job'.format(cwd),
                'time': 4,
                'task': 'generate_sitemaps',
                'type': 'hourly',
            },
            {
                'name': '{}_janeway_reader_notifications'.format(cwd),
                'time': 23,
                'task': 'send_publication_notifications',
                'type': 'daily',
            },
            {
                'name': '{}_import_ror_data'.format(cwd),
                'day': 3,
                'task': 'import_ror_data',
                'type': 'monthly',
            },
            {
                'name': '{}_match_ror_ids'.format(cwd),
                'day': 4,
                'task': 'match_ror_ids',
                'type': 'monthly',
            },
        ]

        if settings.ENABLE_ENHANCED_MAILGUN_FEATURES:
            jobs.append(
                {
                    'name': '{}_janeway_mailgun_job'.format(cwd),
                    'time': 59,
                    'task': 'check_mailgun_stat',
                    'type': 'mins',
                }
            )

        if settings.SITE_SEARCH_INDEXING_FREQUENCY:
            task_time, task_type = settings.SITE_SEARCH_INDEXING_FREQUENCY
            jobs.append(
                {
                    'name': '{}_site_search_data'.format(cwd),
                    'time': task_time,
                    'task': 'generate_site_search_data',
                    'type': task_type,
                }
            )

        for job in jobs:
            current_job = find_job(tab, job['name'])

            if not current_job:
                django_command = "{0}/manage.py {1}".format(settings.BASE_DIR, job['task'])
                if virtualenv:
                    command = '%s/bin/python3 %s' % (virtualenv, django_command)
                else:
                    command = '%s' % (django_command)

                cron_job = tab.new(command, comment=job['name'])

                if job.get('type') == 'monthly':
                    cron_job.setall('47 2 {} * *'.format(job['day']))
                elif job.get('type') == 'daily':
                    cron_job.setall('0 {} * * *'.format(job['time']))
                elif job.get('type') == 'hourly':
                    cron_job.setall('0 */{} * * *'.format(job['time']))
                else:
                    cron_job.minute.every(job['time'])

            else:
                print("{name} cron job already exists.".format(name=job['name']))

        if action == 'test':
            print(tab.render())
        elif action == 'quiet':
            pass
        else:
            tab.write()

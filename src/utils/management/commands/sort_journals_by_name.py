from django.core.management.base import BaseCommand

from journal import models as models

from utils import setting_handler


class Command(BaseCommand):
    """Sorts journals by their name"""

    help = "Shows a native article ID from a DOI."

    def handle(self, *args, **options):
        """Shows a native system ID

        :param args: None
        :param options: None
        :return: None
        """
        journal_dict = dict()
        name_list = list()
        journals = models.Journal.objects.all()
        for journal in journals:
            name = setting_handler.get_setting('general', 'journal_name', journal).value
            journal_dict[name] = journal.pk,
            name_list.append(name)

        loop = 1
        for name in sorted(name_list):
            pk = journal_dict[name]
            journal = models.Journal.objects.get(pk=pk[0])
            journal.sequence = loop
            journal.save()
            loop = loop + 1

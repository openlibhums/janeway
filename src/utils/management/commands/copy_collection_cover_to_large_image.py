from django.core.management.base import BaseCommand

from journal import models


class Command(BaseCommand):
    """
    A management command that copies, for any given journals, collection cover images into the large image attribute.
    Usage: python3 manage.py copy_collection_cover_to_large_image --journal_codes olh 19 c21
    """

    help = "Copies, for any given journals, collection cover images into the large image attribute."

    def add_arguments(self, parser):
        parser.add_argument('--journal_codes', nargs='+')

    def handle(self, *args, **options):
        journal_codes = options.get('journal_codes')
        print(journal_codes)
        journals = models.Journal.objects.filter(code__in=journal_codes)

        for journal in journals:
            print('Processing {}'.format(journal.name))
            collections = models.Issue.objects.filter(
                issue_type__code='collection',
            )
            for collection in collections:
                print('Processing {}'.format(collection))
                collection.large_image = collection.cover_image
                collection.save()

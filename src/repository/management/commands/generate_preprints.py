import random
from uuid import uuid4
from faker import Faker

from django.utils.text import slugify
from django.utils import timezone
from django.core.management.base import BaseCommand

from core import models as core_models
from repository import models


class Command(BaseCommand):
    """A management command to generate random preprints."""

    help = "Allows an admin to generate random preprints."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('short_name')
        parser.add_argument('number', nargs='?', default=1, type=int)
        parser.add_argument('owner', nargs='?', default=None)
        parser.add_argument(
            '--metrics',
            type=int,
            default=None,
            help="number of PreprintAccess to create by article",
        )

    def handle(self, *args, **options):
        """Allows an admin to generate random preprints"

        :param args: None
        :param options: None
        :return: None
        """
        short_name = options.get('short_name')
        number = options.get('number')
        owner = options.get('owner')
        metrics = options.get('metrics', 0)
        fake = Faker()

        try:
            repo = models.Repository.objects.get(
                short_name=short_name,
            )
        except models.Repository.DoesNotExist:
            exit('No repository found.')

        if owner:
            try:
                owner = core_models.Account.objects.get(pk=owner)
            except core_models.Account.DoesNotExist:
                exit('Owner not found.')
        else:
            owner = core_models.Account.objects.all().first()

        subjects = [
            'Computing',
            'Software Engineering',
            'Web Development',
        ]

        for subject in subjects:
            models.Subject.objects.get_or_create(
                repository=repo,
                name=subject,
                slug=slugify(subject),
                enabled=True,
            )

        subjects = models.Subject.objects.all()

        stages = [
            models.STAGE_PREPRINT_REVIEW,
            models.STAGE_PREPRINT_PUBLISHED,
        ]

        for x in range(0,number):
            preprint = models.Preprint.objects.create(
                repository=repo,
                owner=owner,
                stage=random.choice(stages),
                title=fake.sentence(),
                abstract=fake.text(),
                comments_editor=fake.text(),
                date_submitted=timezone.now(),
            )

            preprint.subject.add(
                random.choice(subjects),
            )

            preprint_file = models.PreprintFile.objects.create(
                preprint=preprint,
                original_filename='fake_file.pdf',
                mime_type='application/pdf',
                size=100,
            )

            preprint.submission_file = preprint_file

            for y in range(0, 1):
                fake_email = '{uuid}@example.com'.format(uuid=uuid4())
                account = core_models.Account.objects.create(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake_email,
                    username=fake_email,
                    institution=fake.sentence(),

                )
                models.PreprintAuthor.objects.create(
                    preprint=preprint,
                    order=y,
                    account=account,
                )

            if preprint.stage == models.STAGE_PREPRINT_PUBLISHED:
                preprint.date_accepted = timezone.now()
                preprint.date_published = timezone.now()

                models.PreprintVersion.objects.create(
                    preprint=preprint,
                    file=preprint_file,
                    version=1,
                    date_time=timezone.now(),
                    title=preprint.title,
                    abstract=preprint.abstract,
                )
            print("Created Preprint %d" % preprint.id)

            if metrics:
                print("Inserting Metrics...")
                models.PreprintAccess.objects.bulk_create([
                    models.PreprintAccess(
                        preprint=preprint,
                        file=preprint_file,
                    ) for i in range(0, metrics)])


            preprint.save()
            print(f"Created {preprint.title} with ID {preprint.pk}")

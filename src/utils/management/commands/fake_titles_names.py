import random
from tqdm import tqdm
from faker import Faker
from django.core.management.base import BaseCommand
from submission.models import Article, FrozenAuthor
from core.models import Account


class Command(BaseCommand):
    help = "Randomise titles for Articles and names for FrozenAuthors and Accounts"

    EXCLUDED_EMAILS = {"olh-tech@bbk.ac.uk", "a.byers@bbk.ac.uk", "tech@openlibhums.org"}

    def handle(self, *args, **kwargs):
        fake = Faker()

        self.stdout.write(self.style.SUCCESS("Updating Article titles..."))
        articles = Article.objects.all()
        for article in tqdm(articles, desc="Updating Articles"):
            article.title = fake.sentence()
            article.save(update_fields=["title"])

        self.stdout.write(self.style.SUCCESS("Updating FrozenAuthor names..."))
        authors = FrozenAuthor.objects.all()
        for author in tqdm(authors, desc="Updating FrozenAuthors"):
            author.first_name = fake.first_name()
            author.last_name = fake.last_name()
            author.save(update_fields=["first_name", "last_name"])

        self.stdout.write(self.style.SUCCESS("Updating Account names..."))
        accounts = Account.objects.exclude(email__in=self.EXCLUDED_EMAILS)
        for account in tqdm(accounts, desc="Updating Accounts"):
            account.first_name = fake.first_name()
            account.last_name = fake.last_name()
            account.save(update_fields=["first_name", "last_name"])

        self.stdout.write(self.style.SUCCESS("Successfully updated all records."))
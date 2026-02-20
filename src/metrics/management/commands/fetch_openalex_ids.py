import time

import requests
from django.core.management.base import BaseCommand

from identifiers import models as im
from journal import models as jm
from submission import models as sm


class Command(BaseCommand):
    """
    Fetches OpenAlex Work IDs for published articles and stores them as
    Identifier objects with id_type="openalex".
    """

    help = "Fetches OpenAlex Work IDs for articles that have a DOI but no OpenAlex identifier."

    def add_arguments(self, parser):
        parser.add_argument(
            "--mailto",
            default="",
            help="Email address for OpenAlex polite pool.",
        )
        parser.add_argument(
            "--journal_code",
            default=None,
            help="Limit to a specific journal by code.",
        )
        parser.add_argument(
            "--article_id",
            type=int,
            default=None,
            help="Fetch a single article by its primary key.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Seconds to wait between requests (default 0.5).",
        )

    def handle(self, *args, **options):
        mailto = options["mailto"]
        journal_code = options["journal_code"]
        article_id = options["article_id"]
        delay = options["delay"]

        articles = sm.Article.objects.filter(
            stage=sm.STAGE_PUBLISHED,
            identifier__id_type="doi",
        ).exclude(
            identifier__id_type="openalex",
        ).distinct()

        if article_id:
            articles = articles.filter(pk=article_id)
        elif journal_code:
            journal = jm.Journal.objects.get(code=journal_code)
            articles = articles.filter(journal=journal)

        total = articles.count()
        self.stdout.write(f"Found {total} articles to process.")

        for i, article in enumerate(articles, start=1):
            doi_identifier = article.identifier_set.filter(id_type="doi").first()
            if not doi_identifier:
                continue

            doi = doi_identifier.identifier
            url = f"https://api.openalex.org/works/https://doi.org/{doi}?select=id"
            if mailto:
                url += f"&mailto={mailto}"

            self.stdout.write(f"[{i}/{total}] {doi}", ending="... ")

            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 404:
                    self.stdout.write("not found, skipping.")
                    time.sleep(delay)
                    continue
                response.raise_for_status()
                data = response.json()
                openalex_url = data.get("id", "")
                # e.g. "https://openalex.org/W2741809807" -> "W2741809807"
                work_id = openalex_url.rstrip("/").split("/")[-1]
                if not work_id:
                    self.stdout.write("no ID in response, skipping.")
                    time.sleep(delay)
                    continue
                im.Identifier.objects.get_or_create(
                    article=article,
                    id_type="openalex",
                    identifier=work_id,
                )
                self.stdout.write(f"stored {work_id}.")
            except requests.RequestException as e:
                self.stdout.write(f"request error: {e}")

            time.sleep(delay)

        self.stdout.write("Done.")

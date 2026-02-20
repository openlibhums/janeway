import time

import requests
from django.core.management.base import BaseCommand

from identifiers import models as im
from journal import models as jm
from metrics import models as mm
from submission import models as sm

OPENALEX_API = "https://api.openalex.org/works"
FIELDS = "id,doi,display_name,publication_year,type,primary_location,biblio"


def _get_source(work):
    primary = work.get("primary_location") or {}
    return primary.get("source") or {}


def _store_article_link(article, work, object_type):
    raw_doi = work.get("doi") or ""
    doi = raw_doi.replace("https://doi.org/", "").strip()
    if not doi:
        return False

    source = _get_source(work)
    biblio = work.get("biblio") or {}

    defaults = {
        "object_type": object_type,
        "source": "openalex",
        "article_title": work.get("display_name") or "",
        "year": work.get("publication_year") or 0,
        "journal_title": source.get("display_name") or "",
        "journal_issn": source.get("issn_l") or "",
        "volume": biblio.get("volume") or "",
        "issue": biblio.get("issue") or "",
    }

    mm.ArticleLink.objects.update_or_create(
        article=article,
        doi=doi,
        defaults=defaults,
    )
    return True


def _store_book_link(article, work):
    raw_doi = work.get("doi") or ""
    doi = raw_doi.replace("https://doi.org/", "").strip()
    if not doi:
        return False

    defaults = {
        "object_type": "book",
        "source": "openalex",
        "title": work.get("display_name") or "",
        "year": work.get("publication_year") or 0,
        "isbn_print": "",
        "isbn_electronic": "",
        "component_number": "",
    }

    mm.BookLink.objects.update_or_create(
        article=article,
        doi=doi,
        defaults=defaults,
    )
    return True


class Command(BaseCommand):
    """
    Fetches citing works from OpenAlex for articles that have an OpenAlex
    identifier and stores them as ArticleLink or BookLink objects.
    """

    help = "Fetches citation data from OpenAlex and stores as ArticleLink/BookLink records."

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
            help="Fetch citations for a single article by its primary key.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Seconds to wait between page requests (default 0.5).",
        )

    def handle(self, *args, **options):
        mailto = options["mailto"]
        journal_code = options["journal_code"]
        article_id = options["article_id"]
        delay = options["delay"]

        articles = sm.Article.objects.filter(
            stage=sm.STAGE_PUBLISHED,
            identifier__id_type="openalex",
        ).distinct()

        if article_id:
            articles = articles.filter(pk=article_id)
        elif journal_code:
            journal = jm.Journal.objects.get(code=journal_code)
            articles = articles.filter(journal=journal)

        total = articles.count()
        self.stdout.write(f"Found {total} articles with OpenAlex IDs.")

        for i, article in enumerate(articles, start=1):
            openalex_id = article.identifier_set.filter(id_type="openalex").first()
            if not openalex_id:
                continue

            work_id = openalex_id.identifier
            self.stdout.write(f"[{i}/{total}] Article {article.pk} ({work_id})")

            cursor = "*"
            page_num = 0
            stored = 0
            skipped = 0

            while cursor:
                params = {
                    "filter": f"cites:{work_id}",
                    "per_page": 200,
                    "cursor": cursor,
                    "select": FIELDS,
                }
                if mailto:
                    params["mailto"] = mailto

                try:
                    response = requests.get(OPENALEX_API, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                except requests.RequestException as e:
                    self.stdout.write(f"  Request error on page {page_num}: {e}")
                    break

                results = data.get("results", [])
                meta = data.get("meta", {})
                page_num += 1
                self.stdout.write(f"  Page {page_num}: {len(results)} works")

                for work in results:
                    work_type = work.get("type") or ""
                    if work_type == "article":
                        ok = _store_article_link(article, work, "article")
                    elif work_type in ("book", "book-chapter"):
                        ok = _store_book_link(article, work)
                    else:
                        ok = _store_article_link(article, work, "other")

                    if ok:
                        stored += 1
                    else:
                        skipped += 1

                time.sleep(delay)

                cursor = meta.get("next_cursor")

            self.stdout.write(
                f"  Stored {stored} links, skipped {skipped} (no DOI)."
            )

        self.stdout.write("Done.")

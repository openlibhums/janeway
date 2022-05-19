from django.core.management.base import BaseCommand

from submission.models import Article
from core.models import File


class Command(BaseCommand):
    """Dumps the text of files to the database using FileText Model"""

    help = """
        Dumps the text of galley files into the database, which populates the
        full-text searching indexes
    """

    def add_arguments(self, parser):
        parser.add_argument('--journal-code', type=int)
        parser.add_argument('--article-id', type=int)
        parser.add_argument('--file-id', type=int)
        parser.add_argument('--all', action="store_true", default=False)

    def handle(self, *args, **options):
        if options["file_id"]:
            file_ = File.objects.get(id=options["file_id"])
            file_.index_full_text()
        elif options["article_id"] or options["journal_code"] or options["all"]:
            articles = Article.objects.all()
            if options["journal_code"]:
                articles = articles.filter(journal__code=options["journal_code"])
            if options["article_id"]:
                articles = articles.filter(id=options["article_id"])

            for article in articles:
                print(f"Processing Article {article.pk}")
                article.index_full_text()

        else:
            self.stderr.write("At least one filtering flag must be provided")
            self.print_help("manage.py", "dump_file_text_to_db.py")

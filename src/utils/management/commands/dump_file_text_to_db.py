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
        parser.add_argument('--journal-code', type=str)
        parser.add_argument('--article-id', type=int)
        parser.add_argument('--file-id', type=int)
        parser.add_argument('--all', action="store_true", default=False)

    def handle(self, *args, **options):
        errors = []
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
                try:
                    article.index_full_text()
                except Exception as e:
                    self.stderr.write("%s" % e)
                    errors.append((article.id, e))
        if errors:
            self.stderr.write("Errors Found:")
            for id, err in errors:
                self.stderr.write("%d: %s" % (id, repr(err)))

        else:
            self.stderr.write("At least one filtering flag must be provided")
            self.print_help("manage.py", "dump_file_text_to_db.py")

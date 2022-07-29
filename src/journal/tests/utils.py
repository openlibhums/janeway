from journal.models import Journal
from django.db.utils import IntegrityError
from utils.install import update_settings, update_xsl_files


def make_test_journal(**kwargs):
    try:
        update_xsl_files()
        update_settings()
        journal = Journal(**kwargs)
        journal.save()
    except IntegrityError:
        pass

    return journal

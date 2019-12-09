from journal.models import Journal
from django.db.utils import IntegrityError
from utils.install import update_settings, update_xsl_files

def make_test_journal(**kwargs):
    try:
        update_xsl_files()
        journal = Journal(**kwargs)
        journal.save()

        update_settings(journal, management_command=False)
    except IntegrityError:
        pass


    return journal


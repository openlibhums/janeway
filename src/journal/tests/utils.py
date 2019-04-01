from journal.models import Journal
from django.db.utils import IntegrityError
from utils.install import update_settings

def make_test_journal(**kwargs):
    try:
        journal = Journal(**kwargs)
        journal.save()
        update_settings(journal, management_command=False)
    except IntegrityError:
        pass


    return journal


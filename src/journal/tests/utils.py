from journal.models import Journal
from utils.install import update_settings

def make_test_journal(**kwargs):
    journal = Journal(**kwargs)
    journal.save()
    update_settings(journal, management_command=False)

    return journal


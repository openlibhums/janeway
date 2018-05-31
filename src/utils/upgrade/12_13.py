from journal import models as journal_models


def run_journal_signals():
    """
    Gets and saves all journal objects forcing them to fire signals, 1.2 -> 1.3 introduced a couple of signales
    so we want them to be fired on upgrade.
    :return: None
    """
    journals = journal_models.Journal.objects.al()

    for journal in journals:
        journal.save()


def execute():
    run_journal_signals()

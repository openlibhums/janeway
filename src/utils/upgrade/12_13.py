from journal import models as journal_models
from submission import models as submission_models


def run_journal_signals():
    """
    Gets and saves all journal objects forcing them to fire signals, 1.2 -> 1.3 introduced a couple of signales
    so we want them to be fired on upgrade.
    :return: None
    """
    print('Processing journal signals')
    journals = journal_models.Journal.objects.all()

    for journal in journals:
        print('Processing {journal_code}'.format(journal_code=journal.code), end='...')
        journal.save()
        print(' [OK]')


def process_article_workflow():
    """
    Processes an article and adds workflow history objects for it.
    :return: None
    """
    print('Processing workflow migration')
    for journal in journal_models.Journal.objects.all():
        print('Working on {journal_code}'.format(journal_code=journal.code))
        for article in submission_models.Article.objects.filter(journal=journal):
            stage_log_objects = submission_models.ArticleStageLog.objects.filter(article=article)


def execute():
    run_journal_signals()
    process_article_workflow()
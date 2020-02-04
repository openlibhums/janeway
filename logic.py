from production import logic


def production_ready_files(article):
    """
    Gathers a list of production ready files.
    :param article: an Article object
    :return: a list of File type objects
    """
    submitted_ms_files = article.manuscript_files.filter(is_galley=False)
    copyeditted_files = logic.get_copyedit_files(article)

    return {
        'Manuscript File': submitted_ms_files,
        'Copyedited File': copyeditted_files,
    }

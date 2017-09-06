from journal import models


def yield_homepage_element_context(request, homepage_elements):
    """ Renders a specific issue in the journal.

        :param request: the request associated with this call
        :return: a rendered template of this issue
        """

    if homepage_elements is not None and homepage_elements.filter(name='Current Issue').exists():

        issue_object = request.journal.current_issue

        if issue_object:
            articles = issue_object.articles.all().order_by('section',
                                                            'page_numbers').prefetch_related('authors',
                                                                                             'manuscript_files').select_related(
                'section')

            issue_objects = models.Issue.objects.filter(journal=request.journal)

            context = {
                'issue': issue_object,
                'issues': issue_objects,
                'structure': issue_object.structure(articles),
                'show_sidebar': False
            }

            return context
        else:
            return {}
    else:
        return {}

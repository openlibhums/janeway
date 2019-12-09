from journal import models


def yield_homepage_element_context(request, homepage_elements):
    """ Renders a specific issue in the journal.

        :param request: the request associated with this call
        :return: a rendered template of this issue
        """

    if homepage_elements is not None and homepage_elements.filter(
            name='Current Issue',
    ).exists():

        issue_object = request.journal.current_issue

        if issue_object:

            issue_objects = models.Issue.objects.filter(
                journal=request.journal,
            )

            context = {
                'issue': issue_object,
                'structure': issue_object.structure,  # for compatibility
                'issues': issue_objects,
                'articles': issue_object.get_sorted_articles(),
                'show_sidebar': False,
            }

            return context
        else:
            return {}
    else:
        return {}

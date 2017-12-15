__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(name='About').exists():
        return {'about_content': request.journal.description}
    else:
        return {}

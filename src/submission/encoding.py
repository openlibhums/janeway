
__copyright__ = "Copyright 2022 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.template.loader import get_template


def encode_article_as_bibtex(article):
    context = {"article": article}
    template = get_template('encoding/article_bibtex.bib')
    rendered = template.render(context)

    return rendered


def encode_article_as_ris(article):
    context = {"article": article}
    template = get_template('encoding/article_ris.ris')
    rendered = template.render(context)

    return rendered

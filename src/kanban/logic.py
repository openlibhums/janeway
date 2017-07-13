__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.template.loader import get_template

def create_html_snippet(note):
    template = get_template('elements/notes/note_snippet.html')
    html_content = template.render({'note': note})

    return html_content

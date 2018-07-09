__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import reverse
from django.shortcuts import redirect

from security.decorators import editor_user_required


@editor_user_required
def featured_journals(request):
    reverse_url = '{url}#id_random_featured_journals'.format(url=reverse('press_edit_press'))
    return redirect(reverse_url)

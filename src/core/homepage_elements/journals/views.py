__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.shortcuts import redirect


@staff_member_required
def featured_journals(request):
    reverse_url = '{url}#id_random_featured_journals'.format(url=reverse('press_edit_press'))
    return redirect(reverse_url)

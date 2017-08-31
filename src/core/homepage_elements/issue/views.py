from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.shortcuts import redirect


@staff_member_required
def current_issue(request):

    return redirect(reverse('home_settings_index'))

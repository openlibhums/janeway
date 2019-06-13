from django.urls import reverse
from django.shortcuts import redirect

from security.decorators import editor_user_required


@editor_user_required
def current_issue(request):
    return redirect(reverse('home_settings_index'))

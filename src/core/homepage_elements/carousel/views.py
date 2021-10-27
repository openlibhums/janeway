from django.urls import reverse
from django.shortcuts import redirect, render
from core.homepage_elements.carousel import forms

from core import models
from security.decorators import editor_user_required


@editor_user_required
def settings_carousel(request):
    home_form = forms.CarouselForm(
        request=request,
        instance=request.site_type.carousel,
    )

    if request.POST and 'cancel' in request.POST:
        return redirect(reverse('core_manager_index'))

    if request.POST:
        home_form = forms.CarouselForm(
            request.POST,
            request.FILES,
            request=request,
            instance=request.site_type.carousel,
        )

        if home_form.is_valid():
            home_form.save(request=request)
            return redirect(reverse('home_settings_index'))

    template = 'carousel_setup.html'
    context = {
        'settings': [{group.name: models.Setting.objects.filter(group=group).order_by('name')} for group in
                     models.SettingGroup.objects.all().order_by('name')],
        'home_form': home_form
    }

    return render(request, template, context)

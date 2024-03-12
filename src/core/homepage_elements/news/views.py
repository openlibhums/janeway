from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages

from utils import setting_handler, models
from security.decorators import editor_user_required
from core.homepage_elements.news import forms


@editor_user_required
def news_config(request):
    form = forms.NewsForm(journal=request.journal)
    if request.POST:
        form = forms.NewsForm(
            request.POST,
            journal=request.journal,
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.INFO,
                'News settings updated.'
            )
            return redirect(reverse('home_settings_index'))

    template = 'news_settings.html'
    context = {
        'form': form,
    }

    return render(request, template, context)

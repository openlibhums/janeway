from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages

from core.homepage_elements.popular import forms

from security.decorators import editor_user_required


@editor_user_required
def featured_articles(request):
    form = forms.FeaturedForm(journal=request.journal)

    if request.POST:

        if 'form' in request.POST:
            form = forms.FeaturedForm(request.POST, journal=request.journal)

            if form.is_valid():
                form.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Settings saved.',
                )
                return redirect(reverse('popular_articles_setup'))

    template = 'popular_setup.html'
    context = {
        'form': form,
    }

    return render(request, template, context)

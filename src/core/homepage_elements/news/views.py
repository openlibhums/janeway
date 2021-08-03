from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages

from utils import setting_handler, models
from security.decorators import editor_user_required


@editor_user_required
def news_config(request):
    plugin = models.Plugin.objects.get(name='News')
    number_of_articles = setting_handler.get_plugin_setting(
        plugin,
        'number_of_articles',
        request.journal,
        create=True,
        pretty='Number of Articles',
    ).value
    number_of_articles = int(
        number_of_articles
    ) if number_of_articles else 2
    if request.POST:
        number_of_articles = request.POST.get('number_of_articles')
        setting_handler.save_plugin_setting(plugin, 'number_of_articles', number_of_articles, request.journal)
        messages.add_message(request, messages.INFO, 'Number of articles updated.')
        return redirect(reverse('home_settings_index'))

    template = 'news_settings.html'
    context = {
        'number_of_articles': number_of_articles,
    }

    return render(request, template, context)

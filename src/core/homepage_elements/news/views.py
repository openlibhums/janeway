from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages

from utils import setting_handler, models


@staff_member_required
def news_config(request):
    plugin = models.Plugin.objects.get(name='News')
    number_of_articles = setting_handler.get_plugin_setting(plugin, 'number_of_articles', request.journal, create=True,
                                                            pretty='Number of Articles').value
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

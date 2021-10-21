__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages

from utils import setting_handler, models
from security.decorators import editor_user_required


@editor_user_required
def html_settings(request, element_code=None):
    plugin = models.Plugin.objects.get(name='HTML')

    if element_code:
        plugin_group_name = 'plugin:{plugin_name}'.format(plugin_name=plugin.name)
        setting = setting_handler.create_setting(
            setting_group_name=plugin_group_name,
            setting_name=element_code,
            type='rich-text',
            pretty_name='HTML Block Content',
            description=element_code,
            is_translatable=True,
            default_value='<p></p>',
        )
        html_block_content = setting_handler.get_plugin_setting(
            plugin,
            element_code,
            request.journal,
        ).value
    else:
        html_block_content = setting_handler.get_plugin_setting(
            plugin,
            'html_block_content',
            request.journal,
            create=True,
            pretty='HTML Block Content'
        ).value

    if request.POST:
        html_block_content = request.POST.get('html_block_content')
        if element_code:
            setting_handler.save_plugin_setting(plugin,
                                                element_code,
                                                html_block_content,
                                                request.journal)
        else:
            setting_handler.save_plugin_setting(plugin,
                                                'html_block_content',
                                                html_block_content,
                                                request.journal)
        messages.add_message(request, messages.INFO, 'HTML Block updated.')
        return redirect(reverse('home_settings_index'))

    template = 'html_settings.html'
    context = {
        'html_block_content': html_block_content,
        'disable_rich_text': request.GET.get('disable_rich_text', False)
    }

    return render(request, template, context)

__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.template import Template, RequestContext, Context
from utils import setting_handler


def get_message_content(request, context, template, plugin=False, template_is_setting=False):
    if plugin:
        template = setting_handler.get_plugin_setting(plugin, template, None).value
    elif not template_is_setting:
        template = setting_handler.get_setting('email', template, request.journal).value

    template = Template(template)
    con = RequestContext(request)
    con.push(context)
    html_content = template.render(con)

    return html_content


def get_requestless_content(context, journal, template, group_name='email'):

    template = setting_handler.get_setting(group_name, template, journal).value

    template = Template(template)
    html_content = template.render(Context(context))

    return html_content

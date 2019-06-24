from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def render_string(context, string):
	""" Renders the given string as with django Template engine"""
	templ = template.Template(string)
	return templ.render(context)


from django import template

# temporarily commented out
# from utils.orcid import build_redirect_uri

register = template.Library()


# temporarily commented out
# @register.simple_tag(takes_context=True)
# def orcid_redirect_uri(context):
#    request = context.get('request')
#    if request:
#        return build_redirect_uri(request.site_type)
#    else:
#        return ""


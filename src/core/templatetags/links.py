from django import template
from django.conf import settings
from django.template.exceptions import TemplateSyntaxError
from django.utils.safestring import mark_safe
import re
import logging

register = template.Library()
logger = logging.getLogger(__name__)

"""
These link filters take the following general syntax:

{{ link_html|linktype_link }}
{{ link_html|linktype_link:"contextual" }}  # contextual mode (skips a11y check)

They return the corresponding template from common/elements/links/

generic link context values:
block_input: the whole string that was input when calling the filter
content: the html between the <a> tags
attrs: all attributes that haven't been extracted or deleted by mods

context that may be created by mods:
<attr-name>: values for an extracted attribute
inner_html_start: the html up to the closing tags at the end (for positioning of any icons 'after' text but within the link)
inner_html_end: companion to inner_html_start, the closing tags that come after.

"""

# Filters
@register.filter(name='external_link')
def external_link(value, contextual=False):
    modifications = [attr_remove("target"), attr_remove("rel"), attr_extract("class"), split_html_before_last_tags]
    template = 'common/elements/links/external.html'
    return generic_link(value, contextual, modifications, template)

@register.filter(name='internal_link')
def internal_link(value, contextual=False):
    modifications = []
    template = 'common/elements/links/internal.html'
    return generic_link(value, contextual, modifications, template)



def generic_link(value, contextual, modifications, template_src):
    def split_attributes_content(context):
        # Expected pattern: <a attributes>content</a>
        match = re.match(r'^<a\s+([^>]*)>(.*)</a>$', context['block_input'].strip(), re.DOTALL)
        if match:
            context['attrs'] = match.group(1)
            context['content'] = match.group(2)
            return True
        return False

    generic_modifications = [attr_exists("href")]

    # Handle links not marked as contextual, include an a11y check
    if isinstance(contextual, str):
        contextual = contextual.lower() in ('true', '1', 'yes', 'contextual')
    html_string = str(value).strip()
    link_context = {
        'block_input': html_string,
    }
    if not contextual:
        generic_modifications.append(check_a11y)
    
    # modify link context
    split_attributes_content(link_context)
    modifications.extend(generic_modifications)
    for mod in modifications:
        success = mod(link_context)
        if not success:
            mod_name = getattr(mod, '__name__', str(mod))
            error_message = "invalid link syntax: " + mod_name + ", template: " + template_src
            if settings.DEBUG:
                raise TemplateSyntaxError(error_message)
            else:
                logger.error(error_message)
                return mark_safe(link_context['block_input'])  
            
    # Render the template
    t = template.loader.get_template(template_src)
    return mark_safe(t.render(link_context))

# modification helpers
def get_attribute_pattern(attr_name):
    return rf'{attr_name}=["\']([^"\']*)["\']'

# modification generators
def attr_exists(attr: str) -> callable:
    def exists_specific_attr(context):
        pattern = get_attribute_pattern(attr)
        return re.search(pattern, context['attrs'])
    exists_specific_attr.__name__ = f"attr_exists({attr})"
    return exists_specific_attr

def attr_extract(attr: str) -> callable:
    def extract_specific_attr(context):
        pattern = get_attribute_pattern(attr)
        match = re.search(pattern, context['attrs'])
        if match:
            context[attr] = match.group(1)
            context['attrs'] = re.sub(pattern, '', context['attrs']).strip()
        else:
            context[attr] = ""
        return True
    extract_specific_attr.__name__ = f"attr_extract({attr})"
    return extract_specific_attr

def attr_remove(attr: str) -> callable:
    def remove_specific_attr(context):
        pattern = get_attribute_pattern(attr)
        context['attrs'] = re.sub(pattern, '', context['attrs']).strip()
        return True
    remove_specific_attr.__name__ = f"attr_remove({attr})"
    return remove_specific_attr

# modifications
def check_a11y(context):
    """
    Check for accessibility attributes.
    Requires at least one of: aria-label, aria-labelledby, or aria-describedby
    to be present for proper screen reader support.
    """
    aria_labelledby_exists = attr_exists("aria-labelledby")
    aria_describedby_exists = attr_exists("aria-describedby")
    aria_label_exists = attr_exists("aria-label")

    if aria_labelledby_exists(context):
        return True
    if aria_describedby_exists(context):
        return True
    if aria_label_exists(context):
        return True
    return False

def split_html_before_last_tags(context):
    """
    Split HTML content before the final closing tag(s).
    Returns a tuple of (content_before_final_closing_tags, final_closing_tags)
    
    Example:
    Input: '<h2><span>text</span> more</h2>'
    Output: ('<h2><span>text</span> more', '</h2>')
    
    Input: '<h2><span>text more</span></h2>'
    Output: ('<h2><span>text more', '</span></h2>')
    
    Input: '<h2><span>text more <em>and </em> more </span></h2>'
    Output: ('<h2><span>text more <em>and </em> more' , '</span></h2>')

    Input: '<span>text</span> and more'
    Output: ('<span>text</span> and more', '')

    Input: 'text,<span> more text</span> and even more'
    Output: ('text,<span> more text</span> and even more', '')
    """

    def return_default():
        context["inner_html_start"] = context['content']
        context["inner_html_end"] = ""
        return True
    
    if context['content'].rstrip()[-1] != '>':
        return return_default()

    tags = re.findall(r'<[^>]+>', context['content'])
    if not tags:
        return return_default()

    # Find the last closing tag in the content
    last_closing_tag_index = -1
    for i in range(len(tags) - 1, -1, -1):
        if tags[i].startswith('</'):
            last_closing_tag_index = i
            break

    if last_closing_tag_index == -1:
        return return_default()

    # Find the position of the first closing tag in the final set
    # (in case there are multiple adjacent closing tags at the end)
    first_final_closing_tag = tags[last_closing_tag_index]
    first_final_closing_tag_pos = context['content'].rfind(first_final_closing_tag)
    
    # Split the content
    context["inner_html_start"] = context['content'][:first_final_closing_tag_pos]
    context["inner_html_end"] = context['content'][first_final_closing_tag_pos:]
    return True


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
"""

# Filters
@register.filter(name='external_link')
def external_link_filter(value, contextual=False):

    if not value:
        return value
    
    # Convert contextual parameter to boolean if it's a string
    if isinstance(contextual, str):
        contextual = contextual.lower() in ('true', '1', 'yes', 'contextual')
    
    html_string = str(value).strip()

    link_context = {
        'block_input': html_string,
    }
    
    modifications = [check_input_syntax, check_has_href, extract_classes, split_html_before_last_tags]
    if not contextual:
        modifications.append(check_a11y)
    
    for mod in modifications:
        success = mod(link_context)
        if not success:
            mod_name = getattr(mod, '__name__', str(mod))
            error_message = "invalid link syntax: " + mod_name
            if settings.DEBUG:
                raise TemplateSyntaxError(error_message)
            else:
                logger.error(error_message)
                return mark_safe(link_context['block_input'])
    
    # Render the template
    t = template.loader.get_template('common/elements/links/external.html')
    return mark_safe(t.render(link_context))

def process(parser, token, parse_end, mods, template_src):
    bits = token.split_contents()
    contextual = False
    if len(bits) > 1:
        for bit in bits[1:]:
            if bit.strip() == 'contextual':
                contextual = True
                break

    nodelist = parser.parse((parse_end))
    parser.delete_first_token()
    if not contextual:
        mods += [check_a11y]
    return LinkNode(nodelist, template_src, mods)
    
class LinkNode(template.Node):
    def __init__(self, nodelist, template_src, modifications):
        self.nodelist = nodelist
        self.template_src = template_src
        self.modifications = [check_input_syntax, check_has_href] + modifications 

    def render(self, context):
        block_input = self.nodelist.render(context)  

        link_context ={
            'block_input': block_input,
        }

        for mod in self.modifications:
            success = mod(link_context)
            if not success:
                mod_name = getattr(mod, '__name__', str(mod))
                error_message = "Link modification failure: " + mod_name
                if settings.DEBUG:
                    raise TemplateSyntaxError(error_message)
                else:
                    logger.error(error_message)
                    return block_input
        
        t = template.loader.get_template(self.template_src)
        return t.render(link_context)

# Modifications
"""
check_ these do not change the link context
everything else may change it
Modifications return true for continue, and false for error logging.
"""
patterns = {
    'link': r'^<a\s+([^>]*)>(.*)</a>$',
    'href': r'href=["\']([^"\']*)["\']',
    'class' : r'class=["\']([^"\']*)["\']',
    'tag': r'<[^>]+>',
    'aria-label': r'aria-label=["\']([^"\']*)["\']',
    'aria-labelledby': r'aria-labelledby=["\']([^"\']*)["\']',
    'aria-describedby': r'aria-describedby=["\']([^"\']*)["\']',
}

def check_a11y(context):
    """
    Check for accessibility attributes.
    Requires at least one of: aria-label, aria-labelledby, or aria-describedby
    to be present for proper screen reader support.
    """
    aria_labelledby_match = re.search(patterns['aria-labelledby'], context['attrs'])
    if aria_labelledby_match and aria_labelledby_match.group(1).strip():
        return True
    
    aria_describedby_match = re.search(patterns['aria-describedby'], context['attrs'])
    if aria_describedby_match and aria_describedby_match.group(1).strip():
        return True
    
    aria_label_match = re.search(patterns['aria-label'], context['attrs'])
    if aria_label_match and aria_label_match.group(1).strip():
        return True

    return False

def check_has_href(context):
    return re.search(patterns['href'], context['attrs'])

def check_input_syntax(context):
    # Expected pattern: <a attributes>content</a>
    match = re.match(patterns['link'], context['block_input'].strip(), re.DOTALL)
    if match:
        context['attrs'] = match.group(1)
        context['inner_content'] = match.group(2)
        return True
    return False

def extract_classes(context):
    class_match = re.search(patterns['class'], context['attrs'])
    if class_match:
        context['class_names'] = class_match.group(1)
        context['other_attrs'] = re.sub(patterns['class'], '', context['attrs'])
        context['other_attrs'] = context['other_attrs'].strip()
    else:
        context['class_names'] = ""
        context['other_attrs'] = context['attrs']
    return True

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
    """
    def return_default():
        context["inner_html_start"] = context['inner_content']
        context["inner_html_end"] = ""
        return True

    tags = re.findall(patterns['tag'], context['inner_content'])
    if not tags:
        return_default()

    # Find the last closing tag in the content
    last_closing_tag_index = -1
    for i in range(len(tags) - 1, -1, -1):
        if tags[i].startswith('</'):
            last_closing_tag_index = i
            break

    if last_closing_tag_index == -1:
        return_default()

    # Find the position of the first closing tag in the final set
    # (in case there are multiple adjacent closing tags at the end)
    first_final_closing_tag = tags[last_closing_tag_index]
    first_final_closing_tag_pos = context['inner_content'].rfind(first_final_closing_tag)
    
    # Split the content
    context["inner_html_start"] = context['inner_content'][:first_final_closing_tag_pos]
    context["inner_html_end"] = context['inner_content'][first_final_closing_tag_pos:]
    return True


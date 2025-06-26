from django import template
from django.utils.safestring import mark_safe
from django.conf import settings
from django.template.exceptions import TemplateSyntaxError
from urllib.parse import urlparse
import re

register = template.Library()


LINK_TYPES = {
    'action': {
        'template': 'common/elements/a11y/link.html',
        'test': lambda attributes: bool(attributes.get('onclick')),
    },
    'external': {
        'template': 'common/elements/a11y/links/external.html',
        'test': lambda attributes: bool(urlparse(attributes.get('href', '')).netloc),
    },
    'internal': {
        'template': 'common/elements/a11y/links/internal.html',
        'test': lambda attributes: not bool(urlparse(attributes.get('href', '')).netloc),
    },
    'read_more': { #to fix this is circular.
        'template': 'common/elements/a11y/links/read_more.html',
        'test': lambda attributes: attributes.get('link_type') == 'read_more',
    },
    'page': {
        'template': 'common/elements/a11y/links/page.html',
        'test': lambda attributes: attributes.get('href', '').startswith('#') or bool(urlparse(attributes.get('href', '')).fragment)
    },
    'email': {
        'template': 'common/elements/a11y/links/email.html',
        'test': lambda attributes: attributes.get('href', '').startswith('mailto:'),
    },
    'orcid': {
        'template': 'common/elements/a11y/links/orcid.html',
        'test': lambda attributes: attributes.get('href', '').startswith('https://orcid.org/'),
    },
}

def split_html_at_last_tag(html_content):
    """
    Split HTML content at the last opening tag.
    Returns a tuple of (content_before_last_tag, closing_tags)
    
    Example:
    Input: '<h2><span>text</span> more</h2>'
    Output: ('<h2><span>text</span> more', '</h2>')
    
    Input: '<h2><span>text more</span></h2>'
    Output: ('<h2><span>text more', '</span></h2>')
    """
    if not html_content:
        return '', ''
        
    # Find all opening and closing tags
    tag_pattern = r'<[^>]+>'
    tags = re.findall(tag_pattern, html_content)
    
    if not tags:
        return html_content, ''
    
    # Find the last opening tag
    last_opening_tag_index = -1
    for i, tag in enumerate(tags):
        if not tag.startswith('</'):
            last_opening_tag_index = i
    
    if last_opening_tag_index == -1:
        return html_content, ''
    
    # Get the position of the last opening tag
    last_opening_tag = tags[last_opening_tag_index]
    last_opening_tag_pos = html_content.rfind(last_opening_tag)
    
    # Find the position of the first closing tag after the last opening tag
    first_closing_tag_pos = len(html_content)
    for i in range(last_opening_tag_index + 1, len(tags)):
        if tags[i].startswith('</'):
            first_closing_tag_pos = html_content.find(tags[i], last_opening_tag_pos + len(last_opening_tag))
            break
    
    # Split the content
    content_before = html_content[:first_closing_tag_pos]
    closing_tags = html_content[first_closing_tag_pos:]
    
    return content_before, closing_tags

def developer_assist(link_type, href, title, a11y, inner_html, class_names=None, other_attrs=None ):
    ally_errors = []
    attributes_dict = {'href': href, 'title': title, 'a11y': a11y, 'inner_html': inner_html, 'class_names': class_names, 'other_attrs': other_attrs}

    def calculate_link_type():
        for link_type, link_type_data in LINK_TYPES.items():
            if link_type_data['test'](attributes_dict):
                return link_type
        return None
    
    def validate_link_type():
        expected_link_type = None
        for link_type, link_type_data in LINK_TYPES.items():
            if link_type_data['test'](attributes_dict):
                expected_link_type = link_type

        if link_type not in LINK_TYPES:
            ally_errors.append(f"Invalid link type: {link_type}")
        elif link_type != expected_link_type:
            ally_errors.append(f"Link type mismatch: {link_type} != {expected_link_type}")
        elif link_type == 'action' or expected_link_type == 'action':
            ally_errors.append("Actions should be buttons, not links")
        else:
            ally_errors.append(f"Link type unknown error: {link_type}")

    def validate_aria():
        if a11y != 'contextual':
            if a11y is None:
                ally_errors.append("Links should either be contextual, or have ARIA markup.")
                return
            
            if a11y.get('aria-labelledby') is None:
                if a11y.get('aria-describedby') is None:
                    if a11y.get('aria-label') is None:
                        ally_errors.append("Links should either be contextual, or have ARIA markup.")
                else:
                    if a11y.get('aria-label') is not None:
                        ally_errors.append("Aria-describedby is sufficient")
            else:
                if a11y.get('aria-describedby') is not None or a11y.get('aria-label') is not None:
                    ally_errors.append("Aria-labelledby is sufficient")
        else:
            if a11y.get('aria-labelledby') is not None or a11y.get('aria-describedby') is not None or a11y.get('aria-label') is not None:
                ally_errors.append("Contextual links do not need ARIA markup.")
    
    validate_link_type()
    validate_aria()

    if len(ally_errors) > 0:
        error_message = "\n".join(ally_errors)
        error_message = f"A11y Links - {error_message}"
        raise TemplateSyntaxError(error_message)


def prepare_context(link_type, href, title, a11y, inner_html, class_names=None, other_attrs=None ):
    """
    Prepare the context for link templates
    """

    #if settings.DEBUG:
    #    developer_assist(link_type, href, title, a11y, inner_html, class_names, other_attrs)

    other_attrs = other_attrs if other_attrs is not None else ""
    class_names = class_names if class_names is not None else ""

    if a11y != 'contextual': # used to indicate dev had considered A11y, but no ARIA required.
        other_attrs += a11y

    inner_html_start, inner_html_end = split_html_at_last_tag(inner_html)



    return {
        'href': href,
        'title': title,
        'class_names': class_names,
        'other_attrs_string': other_attrs,
        'inner_html_start': inner_html_start,
        'inner_html_end': inner_html_end,
    }

def include_link(link_type, href, title, a11y, inner_html, class_names=None, other_attrs=None ):
    """
    Include a link in the template
    """
    attr = prepare_context(link_type, href, title, a11y, inner_html, class_names, other_attrs)
    template_path = LINK_TYPES[link_type]['template']
    print(f"Attempting to load template: {template_path}")  # Debug line
    try:
        t = template.loader.get_template(template_path)
        print(f"Template loaded successfully: {template_path}")  # Debug line
        rendered = t.render(attr)
        print(f"Template rendered: {rendered}")  # Debug line
        return mark_safe(rendered)
    except Exception as e:
        print(f"Error loading/rendering template {template_path}: {str(e)}")  # Debug line
        # Fallback to basic link for debugging
        return mark_safe(f'<a href="{href}" title="{title}" class="{class_names}">{inner_html}</a>')




"""
The tag name is is used to choose the link type.
Usage: {% <tag name> href title a11y inner_html class_names other_attrs %}

Parameters:
- href: The URL to link to
- title: The title attribute for the link
- a11y: Accessibility attributes
- inner_html: The HTML content inside the link
- class_names: Optional CSS classes as a string
- other_attrs: Optional additional HTML attributes as a string
"""

@register.tag(name='external_link')
def external_link(parser, token):
    """
    Create an external link with proper accessibility attributes that can contain block content.
    All arguments must be named.
    Example: {% external_link href="https://example.com" title="Example" a11y="contextual" class_names="my-class" other_attrs="data-test='test'" %}
    """
    bits = token.split_contents()
    if len(bits) < 4:
        raise TemplateSyntaxError("'external_link' tag requires at least href, title, and a11y arguments")
    
    # Initialize all arguments as None
    href = None
    title = None
    a11y = None
    class_names = None
    other_attrs = None
    
    # Process all arguments
    for bit in bits[1:]:
        if '=' not in bit:
            raise TemplateSyntaxError(f"All arguments must be named. Got: {bit}")
        
        name, value = bit.split('=', 1)
        value = value.strip('"\'')
        
        if name == 'href':
            href = value
        elif name == 'title':
            title = value
        elif name == 'a11y':
            a11y = value
        elif name == 'class_names':
            class_names = value
        elif name == 'other_attrs':
            other_attrs = value
        else:
            raise TemplateSyntaxError(f"Unknown argument: {name}")
    
    # Validate required arguments
    if not all([href, title, a11y]):
        missing = []
        if not href: missing.append('href')
        if not title: missing.append('title')
        if not a11y: missing.append('a11y')
        raise TemplateSyntaxError(f"Missing required arguments: {', '.join(missing)}")
    
    nodelist = parser.parse(('endexternal_link',))
    parser.delete_first_token()
    
    return ExternalLinkNode(href, title, a11y, nodelist, class_names, other_attrs)

class ExternalLinkNode(template.Node):
    def __init__(self, href, title, a11y, nodelist, class_names=None, other_attrs=None):
        self.href = href
        self.title = title
        self.a11y = a11y
        self.nodelist = nodelist
        self.class_names = class_names
        self.other_attrs = other_attrs

    def render(self, context):
        # Resolve any template variables in the attributes
        try:
            href = template.Variable(self.href).resolve(context)
            title = template.Variable(self.title).resolve(context)
            a11y = template.Variable(self.a11y).resolve(context)
            class_names = template.Variable(self.class_names).resolve(context) if self.class_names else None
            other_attrs = template.Variable(self.other_attrs).resolve(context) if self.other_attrs else None
        except template.VariableDoesNotExist:
            # If the variable doesn't exist, use the literal value
            href = self.href
            title = self.title
            a11y = self.a11y
            class_names = self.class_names
            other_attrs = self.other_attrs
        
        inner_html = self.nodelist.render(context)
        context = prepare_context('external', href, title, a11y, inner_html, class_names, other_attrs)
        template_obj = template.loader.get_template('common/elements/a11y/links/external.html')
        return template_obj.render(context)

@register.simple_tag
def read_more_link(href, title, a11y, inner_html, class_names=None, other_attrs=None):
    context = prepare_context(link_type='read_more', href=href, title=title, a11y=a11y, inner_html=inner_html, class_names=class_names, other_attrs=other_attrs)
    template = template.loader.get_template('common/elements/a11y/links/read_more.html')
    return mark_safe(template.render(context))

@register.simple_tag
def internal_link(href, title, a11y, inner_html, class_names=None, other_attrs=None):
    context = prepare_context(link_type='internal', href=href, title=title, a11y=a11y, inner_html=inner_html, class_names=class_names, other_attrs=other_attrs)
    template = template.loader.get_template('common/elements/a11y/links/internal.html')
    return mark_safe(template.render(context))

@register.simple_tag
def page_link(href, title, a11y, inner_html, class_names=None, other_attrs=None):
    context = prepare_context(link_type='page', href=href, title=title, a11y=a11y, inner_html=inner_html, class_names=class_names, other_attrs=other_attrs)
    template = template.loader.get_template('common/elements/a11y/links/page.html')
    return mark_safe(template.render(context))

@register.simple_tag
def email_link(mailto, title, a11y, inner_html, class_names=None, other_attrs=None):
    context = prepare_context(link_type='email', href=mailto, title=title, a11y=a11y, inner_html=inner_html, class_names=class_names, other_attrs=other_attrs)
    template = template.loader.get_template('common/elements/a11y/links/email.html')
    return mark_safe(template.render(context))

@register.simple_tag
def orcid_link(href, title, a11y, inner_html, class_names=None, other_attrs=None):
    context = prepare_context(link_type='orcid', href=href, title=title, a11y=a11y, inner_html=inner_html, class_names=class_names, other_attrs=other_attrs)
    template = template.loader.get_template('common/elements/a11y/links/orcid.html')
    return mark_safe(template.render(context))


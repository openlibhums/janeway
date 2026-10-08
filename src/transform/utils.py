import os

from lxml import etree, html as lxml_html

from django.conf import settings
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe

from utils.logger import get_logger

logger = get_logger(__name__)


def _apply_html_to_jats_xsl(xsl_name, html_string):
    xslt_path = os.path.join(
        settings.BASE_DIR,
        "transform",
        "xsl",
        xsl_name,
    )

    with open(xslt_path, "rb") as f:
        xslt_doc = etree.parse(f)

    transform = etree.XSLT(xslt_doc)

    wrapped_html = f"<root>{html_string}</root>"
    html_doc = lxml_html.fromstring(wrapped_html)

    result = transform(html_doc)

    # Return the entire transformed result as string
    xml_str = str(result).strip()

    # Optionally clean redundant namespace
    xml_str = xml_str.replace(' xmlns:xlink="http://www.w3.org/1999/xlink"', "")
    xml_str = xml_str.replace("<root>", "").replace("</root>", "").strip()
    return xml_str


def convert_html_abstract_to_jats(abstract_string):
    if not abstract_string:
        return ""

    try:
        return mark_safe(
            _apply_html_to_jats_xsl("html_abstract_to_jats.xsl", abstract_string)
        )

    except Exception as e:
        logger.error(e)
        return ""


def convert_html_title_to_jats(title_string):
    """
    Converts the inline HTML allowed in titles to JATS elements for use
    inside <article-title>. Falls back to the escaped plain text title if
    the transform fails, so the title is never lost.
    """
    if not title_string:
        return ""

    try:
        return mark_safe(
            _apply_html_to_jats_xsl("html_title_to_jats.xsl", title_string)
        )

    except Exception as e:
        logger.error(e)
        return escape(strip_tags(title_string))

import os

from lxml import etree

from django.conf import settings
from django.utils.safestring import mark_safe

from utils.logger import get_logger
logger = get_logger(__name__)

def convert_html_abstract_to_jats(abstract_string):
    if not abstract_string:
        return ""

    try:
        xslt_path = os.path.join(
            settings.BASE_DIR,
            "transform",
            "xsl",
            "html_abstract_to_jats.xsl",
        )

        with open(xslt_path, "rb") as f:
            xslt_doc = etree.parse(f)

        transform = etree.XSLT(xslt_doc)

        wrapped_html = f"<root>{abstract_string}</root>"
        html_doc = etree.XML(wrapped_html.encode("utf-8"))

        result = transform(html_doc)

        # Return the entire transformed result as string
        xml_str = str(result).strip()

        # Optionally clean redundant namespace
        xml_str = xml_str.replace(' xmlns:xlink="http://www.w3.org/1999/xlink"', "")
        xml_str = xml_str.replace("<root>", "").replace("</root>", "").strip()

        return mark_safe(xml_str)

    except Exception as e:
        logger.error(e)
        return ""

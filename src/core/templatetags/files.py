import os

from django import template
from django.template.defaultfilters import filesizeformat

from bs4 import BeautifulSoup

from core import models

register = template.Library()


@register.simple_tag()
def file_size(file, article):
    try:
        return filesizeformat(file.get_file_size(article))
    except BaseException:
        return 0


@register.simple_tag()
def has_missing_supplements(galley):
    xml_file_contents = galley.file.get_file(galley.article)

    souped_xml = BeautifulSoup(xml_file_contents, 'lxml')

    elements = {
        'img': 'src',
        'graphic': 'xlink:href'
    }

    missing_elements = []

    # iterate over all found elements
    for element, attribute in elements.items():
        images = souped_xml.findAll(element)

        # iterate over all found elements of each type in the elements dictionary
        for idx, val in enumerate(images):
            # attempt to pull a URL from the specified attribute
            url = os.path.basename(val.get(attribute, None))

            try:
                galley.images.get(original_filename=url)
            except models.File.DoesNotExist:
                missing_elements.append(url)

    if not missing_elements:
        return False
    else:
        return missing_elements

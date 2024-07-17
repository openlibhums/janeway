import os

from django import template
from django.core.exceptions import FieldError
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


@register.simple_tag()
def file_type(article, file):

    from production.logic import get_copyedit_files
    copyedited_files = get_copyedit_files(article)
    galley_files = {galley.file for galley in article.galley_set.all()}
    supplementary_files = {
        supp.file for supp in article.supplementary_files.all()
    }
    galley_sub_files = list()
    review_files = {
        review.review_file for review in article.reviewassignment_set.all()
    }
    try:
        # GalleyProofing belongs to the typesetting plugin
        annotated_files = models.File.objects.filter(
            galleyproofing__round__article=article,
        )
    except FieldError:
        annotated_files = models.File.objects.none(
            proofingtask__round__article=article,
        )

    for galley in article.galley_set.all():
        for image in galley.images.all():
            galley_sub_files.append(image)
        if galley.css_file:
            galley_sub_files.append(galley.css_file)

    if file in galley_files:
        return 'Galley'
    if file in supplementary_files:
        return 'Supplementary'
    if file in article.manuscript_files.all():
        return 'Manuscript'
    if file in article.data_figure_files.all():
        return 'Data/Figure'
    if file in annotated_files:
        return 'Proofing'
    if file in copyedited_files:
        return 'Copyedit'
    if file in galley_sub_files:
        return 'Galley Sub File'
    if file in review_files:
        return 'Review Comment'
    return 'Other'

@register.filter()
def filter_html_downloads(galleys):
    if galleys and galleys[0].article.journal.disable_html_downloads is True:
        galleys = [
            galley for galley in galleys
            if galley.file.label != 'HTML'
        ]

    return galleys

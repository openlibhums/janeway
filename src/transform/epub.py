__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os
import codecs
import uuid

from bs4 import BeautifulSoup
from ebooklib import epub

from django.conf import settings

from core import files
from core import models


def temp_directory():
    _dir = os.path.join(settings.BASE_DIR, 'files/temp', str(uuid.uuid4()))
    os.makedirs(_dir, 0o775)
    return _dir


def manipulate_images(html):
    souped_html = BeautifulSoup(str(html), 'html')

    elements = {
        'img': 'src',
    }

    found_elements = []

    # iterate over all found elements
    for element, attribute in elements.items():
        images = souped_html.findAll(element)

        # iterate over all found elements of each type in the elements dictionary
        for image in images:
            # attempt to pull a URL from the specified attribute
            found_elements.append(os.path.basename(image['src']))
            image['src'] = os.path.basename(image['src'])

    css_tag = souped_html.new_tag("link", rel="stylesheet", type="text/css", href="style/default.css")
    souped_html.body.append(css_tag)

    return souped_html, found_elements


def get_html_content(galley):
    if galley.file.mime_type == 'application/xml':
        return galley.render()
    elif galley.file.mime_type == 'text/html':
        return galley.file.get_file(galley.article)


def write_html_to_temp(html, temp):
    file = codecs.open(os.path.join(temp, 'temp.html'), "w", "utf-8")
    file.write(str(html))
    file.close()


def store_file(request, temp, file, galley):
    new_file = files.copy_local_file_to_article(os.path.join(temp, file), 'article.epub', galley.article,
                                                request.user, label="EPUB", galley=True)
    galley.article.manuscript_files.add(new_file)

    models.Galley.objects.create(
        article=galley.article,
        file=new_file,
        label='EPUB',
        type='epub',
        sequence=galley.article.get_next_galley_sequence()
    )


def generate_ebook_lib_epub(request, galley):
    base_html = get_html_content(galley)
    temp = temp_directory()
    file = "temp.epub"
    article = galley.article
    html, elements = manipulate_images(base_html)

    book = epub.EpubBook()

    # add metadata
    book.set_identifier('sample123456')
    book.set_title(article.title)
    book.set_language('en')

    for author in article.authors.all():
        book.add_author(author.full_name())

    c1 = epub.EpubHtml(title=article.title, file_name='article.xhtml', lang='en')
    c1.content = str(html)
    book.add_item(c1)

    for i, element in enumerate(elements):
        img = galley.images.get(original_filename=element)
        item = epub.EpubItem(uid="image_{0}".format(i),
                             file_name=element,
                             content=open(img.self_article_path(), 'rb').read())

        book.add_item(item)

    style = '''img {max-width: 100%;}'''
    default_css = epub.EpubItem(uid="style_default", file_name="style/default.css", media_type="text/css",
                                content=style)
    book.add_item(default_css)

    book.spine = [c1]
    epub.write_epub(os.path.join(temp, file), book, {})

    store_file(request, temp, file, galley)
